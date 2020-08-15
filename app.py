from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ssm as ssm,
    aws_elasticache as ec,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticloadbalancingv2 as elb,
    core,
)

class CosmosBot(core.Stack):

    def __init__(self, scope: core.Construct, id: str, env: core.Environment, **kwargs) -> None:
        super().__init__(scope, id, env=env, *kwargs)

        # Create a /16 VPC with 1 public and private subnet
        # CIDR range will be divided evenly among subnets
        vpc = ec2.Vpc(
            self, 'bot-vpc',
            max_azs=2
        )

        # Create a Redis instance
        redis_security_group = ec2.SecurityGroup(
            self, 'redis-security-group',
            vpc=vpc
        )
        redis_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(6379),
            description='Allow connection from within VPC'
        )

        redis_subnetgroup = ec.CfnSubnetGroup(
            self, 'redis-subnetgroup',
            description="Group of private subnets from the VPC",
            subnet_ids=[ps.subnet_id for ps in vpc.private_subnets]
        )

        redis_cluster = ec.CfnCacheCluster(
            self, 'redis-cluster',
            cache_node_type='cache.t2.small',
            engine='redis',
            num_cache_nodes=1,
            port=6379,
            cache_subnet_group_name=redis_subnetgroup.ref,
            vpc_security_group_ids=[redis_security_group.security_group_id]
        )
        redis_cluster.add_depends_on(redis_subnetgroup)

        #  Create a cluster
        cluster = ecs.Cluster(
            self, 'bot-cluster',
            vpc=vpc
        )

        # Create a Worker task definition
        worker_logging = ecs.AwsLogDriver(stream_prefix='worker')

        worker_task = ecs.FargateTaskDefinition(
            self, 'worker-task',
            cpu=256,
            memory_limit_mib=512
        )
        worker_task.add_container(
            id='worker-container',
            image=ecs.ContainerImage.from_registry('leonweecs/cosmos-worker:1.1'),
            environment={
                'REDIS_HOST': redis_cluster.attr_redis_endpoint_address,
                'REDIS_PORT': redis_cluster.attr_redis_endpoint_port
            },
            logging=worker_logging
        ).add_port_mappings(
            ecs.PortMapping(
                container_port=80,
                host_port=80
            )
        )

        # Create Worker Service
        worker_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, 'worker-service',
            cluster=cluster,
            assign_public_ip=False,
            cpu=256,
            memory_limit_mib=512,
            task_definition=worker_task,
            desired_count=1,
            protocol=elb.ApplicationProtocol.HTTP # HTTPS requires valid domain name and SSL certificate
        )

        # Add a rule to allow ELB to talk with containers
        worker_service.service.connections.security_groups[0].add_ingress_rule(
            peer = ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection = ec2.Port.tcp(80),
            description='Allow http inbound from VPC'
        )

        # Configure ELB health check route
        worker_service.target_group.configure_health_check(
            path='/worker',
            healthy_http_codes='200-299',
        )

        # Setup AutoScaling policy
        scaling = worker_service.service.auto_scale_task_count(
            max_capacity=3
        )
        scaling.scale_on_cpu_utilization(
            'CpuScaling',
            target_utilization_percent=65,
            scale_in_cooldown=core.Duration.seconds(60),
            scale_out_cooldown=core.Duration.seconds(60),
        )

        # Create a MX task definition
        mx_logging = ecs.AwsLogDriver(stream_prefix='mx')

        mx_task = ecs.FargateTaskDefinition(
            self, 'mx-task',
            cpu=256,
            memory_limit_mib=512
        )
        mx_task.add_container(
            id='mx-container',
            image=ecs.ContainerImage.from_registry('leonweecs/cosmos-mx:1.1'),
            environment={
                'REDIS_HOST': redis_cluster.attr_redis_endpoint_address,
                'REDIS_PORT': redis_cluster.attr_redis_endpoint_port,
                'WORKER_HOST': worker_service.load_balancer.load_balancer_dns_name,
                'WORKER_PORT': '80',
                'API_ID': ssm.StringParameter.value_for_string_parameter(self, "API_ID"),
                'API_HASH': ssm.StringParameter.value_for_string_parameter(self, "API_HASH"),
                'BOT_TOKEN': ssm.StringParameter.value_for_string_parameter(self, "BOT_TOKEN"),
            },
            logging=mx_logging
        )

        # Create a MX service
        mx_security_group = ec2.SecurityGroup(
            self, 'mx-security-group',
            vpc=vpc
        )

        mx_service = ecs.FargateService(
            self, 'mx-service',
            task_definition=mx_task,
            assign_public_ip=True,
            security_group=mx_security_group,
            cluster=cluster
        )

        core.CfnOutput(
            self, "LoadBalancerDNS",
            value=worker_service.load_balancer.load_balancer_dns_name
        )

app = core.App()
env = core.Environment(account='839234112409' ,region='ap-southeast-2')
CosmosBot(app, 'CoSMoS-Bot', env)
app.synth()