package tasks

import (
	"context"
	"fmt"
	"sync"
	"time"

	types "github.com/raghavyuva/nixopus-api/internal/features/deploy/types"
	"github.com/raghavyuva/nixopus-api/internal/queue"
	shared_types "github.com/raghavyuva/nixopus-api/internal/types"
	"github.com/vmihailenco/taskq/v3"
)

var (
	onceQueues            sync.Once
	CreateDeploymentQueue taskq.Queue
	TaskCreateDeployment  *taskq.Task
	UpdateDeploymentQueue taskq.Queue
	TaskUpdateDeployment  *taskq.Task
)

var (
	TASK_CREATE_DEPLOYMENT  = "task_create_deployment"
	QUEUE_CREATE_DEPLOYMENT = "create-deployment"
	QUEUE_UPDATE_DEPLOYMENT = "update-deployment"
	TASK_UPDATE_DEPLOYMENT  = "task_update_deployment"
)

func (t *TaskService) SetupCreateDeploymentQueue() {
	onceQueues.Do(func() {
		CreateDeploymentQueue = queue.RegisterQueue(&taskq.QueueOptions{
			Name:                QUEUE_CREATE_DEPLOYMENT,
			ConsumerIdleTimeout: 10 * time.Minute,
			MinNumWorker:        1,
			MaxNumWorker:        10,
			ReservationSize:     10,
			ReservationTimeout:  10 * time.Second,
			WaitTimeout:         5 * time.Second,
			BufferSize:          100,
		})

		TaskCreateDeployment = taskq.RegisterTask(&taskq.TaskOptions{
			Name: TASK_CREATE_DEPLOYMENT,
			Handler: func(ctx context.Context, data shared_types.TaskPayload) error {
				err := t.BuildPack(ctx, data)
				if err != nil {
					return err
				}
				return nil
			},
		})

		UpdateDeploymentQueue = queue.RegisterQueue(&taskq.QueueOptions{
			Name:                QUEUE_UPDATE_DEPLOYMENT,
			ConsumerIdleTimeout: 10 * time.Minute,
			MinNumWorker:        1,
			MaxNumWorker:        10,
			ReservationSize:     10,
			ReservationTimeout:  10 * time.Second,
			WaitTimeout:         5 * time.Second,
			BufferSize:          100,
		})

		TaskUpdateDeployment = taskq.RegisterTask(&taskq.TaskOptions{
			Name: TASK_UPDATE_DEPLOYMENT,
			Handler: func(ctx context.Context, data shared_types.TaskPayload) error {
				fmt.Println("Updating deployment")
				err := t.HandleUpdateDeployment(ctx, data)
				if err != nil {
					return err
				}
				return nil
			},
		})
	})
}

func (t *TaskService) StartConsumers(ctx context.Context) error {
	return queue.StartConsumers(ctx)
}

func (t *TaskService) BuildPack(ctx context.Context, d shared_types.TaskPayload) error {
	var err error
	switch d.Application.BuildPack {
	case shared_types.DockerFile:
		err = t.PrerunCommands(d)
		if err != nil {
			return err
		}
		err = t.HandleCreateDockerfileDeployment(ctx, d)
		if err != nil {
			return err
		}
		err = t.PostRunCommands(d)
		if err != nil {
			return err
		}
	case shared_types.DockerCompose:
		err = t.HandleCreateDockerComposeDeployment(ctx, d)
	case shared_types.Static:
		err = t.HandleCreateStaticDeployment(ctx, d)
	default:
		return types.ErrInvalidBuildPack
	}

	if err != nil {
		return err
	}
	return nil
}
