package main

import (
	"context"
	"flag"
	"log"

	"github.com/raghavyuva/nixopus-api/internal/queue"
)

func main() {
	flag.Parse()

	c := context.Background()

	err := queue.QueueFactory.StartConsumers(c)
	if err != nil {
		log.Fatal(err)
	}

	go queue.LogStats()

	sig := queue.WaitSignal()
	log.Println(sig.String())

	err = queue.QueueFactory.Close()
	if err != nil {
		log.Fatal(err)
	}
}
