from uvicorn import run


if __name__ == "__main__":
    import main
    app = main.app

    run("main:app", host="0.0.0.0", port=9000, reload=True)
