## On Container Creation (Pending State)

Pod Name: ml-job-90-4mq88
Pod Status: Pending
  - Initialized: True
  - Ready: False
  - ContainersReady: False
  - PodScheduled: True
  Container Name: ml-job-90
    Waiting: ContainerCreating

## On Not Started (Queued State)

Pod Name: ml-job-91-nwpfx
Pod Status: Pending
  - PodScheduled: False

## On Failed State

Pod Name: ml-job-93-nvjq8
Pod Status: Failed
  - Initialized: True
  - Ready: False
  - ContainersReady: False
  - PodScheduled: True
  Container Name: ml-job-93
    Terminated: Error

## On Started State (Running)

Pod Name: ml-job-92-8nzbm
Pod Status: Running
  - Initialized: True
  - Ready: True
  - ContainersReady: True
  - PodScheduled: True
  Container Name: ml-job-92
    Running

## On Completed State

Pod Name: ml-job-90-4mq88
Pod Status: Succeeded
  - Initialized: True
  - Ready: False
  - ContainersReady: False
  - PodScheduled: True
  Container Name: ml-job-90
    Terminated: Completed