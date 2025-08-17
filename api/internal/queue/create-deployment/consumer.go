package main

import (
	"context"
	"log"
	"sync/atomic"
	"time"

	"github.com/raghavyuva/nixopus-api/internal/queue"
)

func StartConsumer(ctx context.Context) error {
	err := queue.QueueFactory.StartConsumers(ctx)
	if err != nil {
		return err
	}

	go LogStats()
	log.Println("Consumer started successfully")
	return nil
}

func StopConsumer() error {
	return queue.QueueFactory.Close()
}

var counter int32

func GetLocalCounter() int32 {
	return atomic.LoadInt32(&counter)
}

func IncrLocalCounter() {
	atomic.AddInt32(&counter, 1)
}

func LogStats() {
	var prev int32
	for range time.Tick(3 * time.Second) {
		n := GetLocalCounter()
		log.Printf("processed %d tasks (%d/s)", n, (n-prev)/3)
		prev = n
	}
}
