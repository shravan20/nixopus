package producer

import (
	"context"
	"flag"
	"log"
)

func main() {
	flag.Parse()

	go LogStats()

	go func() {
		for {
			err := MainQueue.Add(CountTask.WithArgs(context.Background()))
			if err != nil {
				log.Fatal(err)
			}
			IncrLocalCounter()
		}
	}()

	sig := WaitSignal()
	log.Println(sig.String())
}