package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/redis/go-redis/extra/redisrate"
	"github.com/redis/go-redis/v9"
	"github.com/raghavyuva/nixopus-api/internal/queue"
	"github.com/vmihailenco/taskq/v3"
)

var CreateDeploymentQueue = queue.RegisterQueue(&taskq.QueueOptions{
	Name:                 "create-deployment",
	ConsumerIdleTimeout:  10 * time.Minute,
	MinNumWorker:         1,
	MaxNumWorker:         10,
	MaxNumFetcher:        10,
	ReservationSize:      10,
	ReservationTimeout:   10 * time.Second,
	WaitTimeout:          10 * time.Second,
	BufferSize:           100,
	PauseErrorsThreshold: 100,
	RateLimit: redisrate.Limit{
		Rate:   100,
		Burst:  100,
		Period: 1 * time.Second,
	},
	RateLimiter: redisrate.NewLimiter(redis.NewClient(&redis.Options{Addr: ":6379"})),
})

var Task1 = taskq.RegisterTask(&taskq.TaskOptions{
	Name: "task1",
	Handler: func(ctx context.Context, arg1, arg2 string) error {
		fmt.Printf("task1 is running with args: %s, %s\n", arg1, arg2)
		IncrLocalCounter()
		return nil
	},
})

var Task2 = taskq.RegisterTask(&taskq.TaskOptions{
	Name: "task2",
	Handler: func(ctx context.Context, arg3, arg4 string) error {
		fmt.Printf("task2 is running with args: %s, %s\n", arg3, arg4)
		IncrLocalCounter()
		return nil
	},
})

func WaitSignal() os.Signal {
	ch := make(chan os.Signal, 2)
	signal.Notify(ch, syscall.SIGINT, syscall.SIGTERM)
	return <-ch
}

func main() {
	ctx := context.Background()

	// Initialize queue with a shared client for this example.
	client := redis.NewClient(&redis.Options{Addr: ":6379"})
	queue.Init(client)

	pong, err := client.Ping(ctx).Result()
	if err != nil {
		fmt.Printf("Failed to connect to Redis: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("Redis connection successful: %s\n", pong)

	err = StartConsumer(ctx)
	if err != nil {
		fmt.Printf("Failed to start consumers: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("Started consumers, beginning task production")

	go func() {
		for {
			err1 := CreateDeploymentQueue.Add(Task1.WithArgs(context.Background(), "arg1", "arg2"))
			if err1 != nil {
				fmt.Printf("Failed to add Task1: %v\n", err1)
			}

			err2 := CreateDeploymentQueue.Add(Task2.WithArgs(context.Background(), "arg3", "arg4"))
			if err2 != nil {
				fmt.Printf("Failed to add Task2: %v\n", err2)
			}

			time.Sleep(1 * time.Second)
		}
	}()

	go func() {
		for range time.Tick(5 * time.Second) {
			fmt.Printf("Local task counter: %d\n", GetLocalCounter())
		}
	}()

	fmt.Println("Producer started. Press Ctrl+C to stop...")
	signal := WaitSignal()
	fmt.Printf("Received signal: %v\n", signal)

	err = StopConsumer()
	if err != nil {
		fmt.Printf("Error closing queue factory: %v\n", err)
	}
}
