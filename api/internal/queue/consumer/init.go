package consumer

import (
	"context"
	"flag"
	"log"
)

func main() {
	flag.Parse()

	c := context.Background()

	err := QueueFactory.StartConsumers(c)
	if err != nil {
		log.Fatal(err)
	}

	go LogStats()

	sig := WaitSignal()
	log.Println(sig.String())

	err = QueueFactory.Close()
	if err != nil {
		log.Fatal(err)
	}
}