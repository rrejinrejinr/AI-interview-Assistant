# Docker, Kubernetes & Cloud DevOps

## Containers vs Virtual Machines
Virtual Machines (VMs) run full guest operating systems on top of a hypervisor, consuming significant memory and compute overhead.
Containers share the host operating system kernel and isolate user space using Linux cgroups and namespaces, offering lightweight, sub-second startup and high reproducibility.

## Docker Best Practices
- Use official minimal base images (e.g. `python:3.11-slim` or `alpine`).
- Leverage multi-stage builds to exclude build tools and compilers from the final production image.
- Order `Dockerfile` instructions from least frequently changed to most frequently changed to maximize Docker layer caching.
- Avoid running containers as `root` user for security hardening.

## Kubernetes Orchestration Core Concepts
- Pod: The smallest deployable computing unit, encapsulating one or more containers.
- Deployment: Manages declarative desired state, replica counts, rolling updates, and rollbacks for stateless workloads.
- Service: Provides stable networking, DNS, and load balancing across dynamic pod IPs (ClusterIP, NodePort, LoadBalancer).
