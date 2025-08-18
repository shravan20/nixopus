package queue

import (
	"context"
	"log"
	"sync"
	"time"

	"github.com/vmihailenco/taskq/v3"
)

var (
	onceQueues sync.Once
	// Queues - Task Pairs
	CreateDeploymentQueue taskq.Queue
	TaskCreateDeployment  *taskq.Task

	HelloWorldQueue taskq.Queue
	TaskHelloWorld  *taskq.Task
)

// SetupQueues registers queues-tasks par with redis and starts consumers.
func SetupQueues() {
	onceQueues.Do(func() {
		// Queue Nanme: Create Deployment
		CreateDeploymentQueue = RegisterQueue(&taskq.QueueOptions{
			Name:                "create-deployment",
			ConsumerIdleTimeout: 10 * time.Minute,
			MinNumWorker:        1,
			MaxNumWorker:        10,
			MaxNumFetcher:       5,
			ReservationSize:     10,
			ReservationTimeout:  10 * time.Second,
			WaitTimeout:         10 * time.Second,
			BufferSize:          100,
		})

		// Queue Name: Hello World
		HelloWorldQueue = RegisterQueue(&taskq.QueueOptions{
			Name:                "hello-world",
			ConsumerIdleTimeout: 10 * time.Minute,
			MinNumWorker:        1,
			MaxNumWorker:        5,
			MaxNumFetcher:       2,
			ReservationSize:     5,
			ReservationTimeout:  10 * time.Second,
			WaitTimeout:         10 * time.Second,
			BufferSize:          50,
		})

		// Task for Create Deployment queue name
		TaskCreateDeployment = taskq.RegisterTask(&taskq.TaskOptions{
			Name: "task_create_deployment",
			Handler: func(ctx context.Context, data PrepareContextResult) error {
				log.Printf("[QUEUE:create-deployment] handling deployment for applicationID=%s", data)
				// TODO: wire deploy service logic call.
				return nil
			},
		})

		// Task for Hello World queue anme
		TaskHelloWorld = taskq.RegisterTask(&taskq.TaskOptions{
			Name: "task_hello_world",
			Handler: func(ctx context.Context, message string) error {
				log.Printf("[QUEUE:hello-world] %s", message)
				return nil
			},
		})
	})
}

// TODO: use in service functions to add messages to the queues
func EnqueueCreateDeployment(ctx context.Context, applicationID string) error {
	return CreateDeploymentQueue.Add(TaskCreateDeployment.WithArgs(ctx, applicationID))
}

func EnqueueHelloWorld(ctx context.Context, message string) error {
	return HelloWorldQueue.Add(TaskHelloWorld.WithArgs(ctx, message))
}
