def build_autoencoder(
    window_size: int,
    n_features: int = 1,
    learning_rate: float = 0.001,
):
    try:
        from tensorflow.keras.layers import Dense, Input, LSTM, RepeatVector, TimeDistributed
        from tensorflow.keras.models import Model
        from tensorflow.keras.optimizers import Adam
    except ImportError as exc:
        raise RuntimeError(
            "TensorFlow o'rnatilmagan. `pip install -r requirements.txt` ni ishga tushiring."
        ) from exc

    inputs = Input(shape=(window_size, n_features))
    encoded = LSTM(64, activation="relu", return_sequences=True)(inputs)
    encoded = LSTM(32, activation="relu", return_sequences=False)(encoded)

    decoded = RepeatVector(window_size)(encoded)
    decoded = LSTM(32, activation="relu", return_sequences=True)(decoded)
    decoded = LSTM(64, activation="relu", return_sequences=True)(decoded)
    decoded = TimeDistributed(Dense(n_features))(decoded)

    model = Model(inputs, decoded)
    model.compile(optimizer=Adam(learning_rate=learning_rate), loss="mse")
    return model
