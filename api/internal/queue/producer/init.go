package main

import (
	"context"
	"flag"
	"log"

	"github.com/raghavyuva/nixopus-api/internal/queue"
)

func main() {
	flag.Parse()

	go queue.LogStats()

	go func() {
		for {
			err := queue.MainQueue.Add(queue.CountTask.WithArgs(context.Background()))
			if err != nil {
				log.Fatal(err)
			}
			queue.IncrLocalCounter()
		}
	}()

	sig := queue.WaitSignal()
	log.Println(sig.String())
}
