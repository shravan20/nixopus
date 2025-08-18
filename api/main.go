package main

import (
	"context"
	"log"
	"net/http"

	"github.com/joho/godotenv"
	"github.com/raghavyuva/nixopus-api/internal"
	"github.com/raghavyuva/nixopus-api/internal/config"
	_ "github.com/raghavyuva/nixopus-api/internal/log"
	"github.com/raghavyuva/nixopus-api/internal/queue"
	"github.com/raghavyuva/nixopus-api/internal/redisclient"
	"github.com/raghavyuva/nixopus-api/internal/storage"
	"github.com/raghavyuva/nixopus-api/internal/types"
)

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file")
	}

	store := config.Init()
	ctx := context.Background()
	app := storage.NewApp(&types.Config{}, store, ctx)

	// Initialize task queue (Redis) and start consumers alongside the server
	redisClient, err := redisclient.New(config.AppConfig.RedisURL)
	if err != nil {
		log.Fatalf("failed to create redis client for queue due to %v", err)
	}
	queue.Init(redisClient)

	// boot independent queues and their tasks before starting consumers
	queue.SetupQueues()
	go func() {
		if err := queue.StartConsumers(ctx); err != nil {
			log.Fatalf("failed to start queue consumers due to %v", err)
		}
		log.Println("Queue consumers started")
	}()

	router := internal.NewRouter(app)
	router.Routes()
	log.Printf("Server starting on port %s", config.AppConfig.Port)
	log.Fatal(http.ListenAndServe(":"+config.AppConfig.Port, nil))
}
