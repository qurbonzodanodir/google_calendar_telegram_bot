


if __name__ == "__main__":
    # For now we run the polling bot directly. 
    # Later we can run FastAPI for webhooks.
    import asyncio
    from app.bot import main
    asyncio.run(main())
