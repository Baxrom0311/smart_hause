from pathlib import Path


def train_model(
    model,
    x_train,
    x_test,
    epochs: int,
    batch_size: int,
    model_path: str,
    progress_callback=None,
) -> dict[str, list[float]]:
    try:
        from tensorflow.keras.callbacks import Callback, EarlyStopping, ModelCheckpoint
    except ImportError as exc:
        raise RuntimeError(
            "TensorFlow o'rnatilmagan. `pip install -r requirements.txt` ni ishga tushiring."
        ) from exc

    class StatusCallback(Callback):
        def on_epoch_end(self, epoch, logs=None):
            if progress_callback:
                progress_callback(epoch + 1, epochs, logs or {})

    monitor = "val_loss" if len(x_test) else "loss"
    callbacks = [
        StatusCallback(),
        EarlyStopping(
            monitor=monitor,
            patience=min(10, max(2, epochs // 5 or 1)),
            restore_best_weights=True,
        ),
        ModelCheckpoint(model_path, monitor=monitor, save_best_only=True),
    ]

    fit_kwargs = {
        "x": x_train,
        "y": x_train,
        "epochs": epochs,
        "batch_size": batch_size,
        "callbacks": callbacks,
        "shuffle": False,
        "verbose": 0,
    }
    if len(x_test):
        fit_kwargs["validation_data"] = (x_test, x_test)

    history = model.fit(**fit_kwargs)

    if not Path(model_path).exists():
        model.save(model_path)

    return {key: [float(value) for value in values] for key, values in history.history.items()}
