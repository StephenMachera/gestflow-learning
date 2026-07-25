import numpy as np
import pandas as pd
import tensorflow as tf
import json
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
CSV_FILE       = 'gesture_data.csv'
MODEL_FILE     = 'gesture_classifier.tflite'
LABEL_MAP_FILE = 'label_map.json'
EPOCHS         = 50       # early stopping will cut this short
BATCH_SIZE     = 32
TEST_SIZE      = 0.2
RANDOM_STATE   = 42

# ─────────────────────────────────────────────
# STEP 1 — LOAD AND CLEAN DATA
# ─────────────────────────────────────────────
print("📂 Loading dataset...")
df = pd.read_csv(CSV_FILE)
print(f"   Raw rows loaded: {len(df)}")

# Drop any rows with non-numeric values (stray headers, corrupt rows)
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df = df.dropna()
print(f"   Cleaned rows remaining: {len(df)}")

# ─────────────────────────────────────────────
# STEP 2 — PREPARE FEATURES AND LABELS
# ─────────────────────────────────────────────
X = df.drop(columns=['label']).values.astype(np.float32)
raw_labels = df['label'].values.astype(np.int32)

# Encode labels and save the mapping
le = LabelEncoder()
y = le.fit_transform(raw_labels).astype(np.int32)

# Save label map so inference knows what each number means
label_map = {int(i): int(cls) for i, cls in enumerate(le.classes_)}
with open(LABEL_MAP_FILE, 'w') as f:
    json.dump(label_map, f, indent=2)
print(f"\n🗂️  Label mapping saved to {LABEL_MAP_FILE}:")
for idx, name in label_map.items():
    print(f"   {idx} → {name}")

num_classes = len(label_map)
print(f"\n   Total gesture classes: {num_classes}")
print(f"   Total samples: {len(X)}")

# ─────────────────────────────────────────────
# STEP 3 — SPLIT INTO TRAIN AND TEST
# ─────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=y   # ensures equal gesture representation in both splits
)

print(f"\n📊 Data split:")
print(f"   Training samples:   {len(X_train)}")
print(f"   Test samples:       {len(X_test)}")

# ─────────────────────────────────────────────
# STEP 4 — BUILD THE NEURAL NETWORK
# ─────────────────────────────────────────────
model = tf.keras.models.Sequential([
    tf.keras.layers.Input(shape=(63,)),

    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.3),

    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dropout(0.2),

    tf.keras.layers.Dense(32, activation='relu'),

    tf.keras.layers.Dense(num_classes, activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

print("\n🧠 Model architecture:")
model.summary()

# ─────────────────────────────────────────────
# STEP 5 — TRAIN WITH EARLY STOPPING
# ─────────────────────────────────────────────
early_stopping = tf.keras.callbacks.EarlyStopping(
    monitor='val_accuracy',
    patience=5,
    restore_best_weights=True,
    verbose=1
)

reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(
    monitor='val_loss',
    factor=0.5,
    patience=3,
    verbose=1
)

print("\n🚀 Starting training...")
history = model.fit(
    X_train, y_train,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    validation_data=(X_test, y_test),
    callbacks=[early_stopping, reduce_lr],
    verbose=1
)

# ─────────────────────────────────────────────
# STEP 6 — EVALUATE
# ─────────────────────────────────────────────
test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)

print("\n=========================================")
print(f"🎉 Training Complete!")
print(f"   Epochs run:      {len(history.history['accuracy'])}")
print(f"   Test accuracy:   {test_acc * 100:.2f}%")
print(f"   Test loss:       {test_loss:.4f}")
print("=========================================")

# Per-gesture performance breakdown
y_pred = np.argmax(model.predict(X_test, verbose=0), axis=1)

print("\n📊 Per-gesture performance:")
print(classification_report(
    y_test, y_pred,
    target_names=[str(label_map[i]) for i in range(num_classes)]
))

# Confusion matrix
print("🔢 Confusion matrix:")
cm = confusion_matrix(y_test, y_pred)
print(cm)

# Warn if any gesture is performing poorly
report = classification_report(
    y_test, y_pred,
    target_names=[str(label_map[i]) for i in range(num_classes)],
    output_dict=True
)
print("\n⚠️  Gestures below 90% accuracy:")
found_weak = False
for gesture, metrics in report.items():
    if isinstance(metrics, dict):
        if metrics.get('f1-score', 1.0) < 0.90:
            print(f"   {gesture} → f1: {metrics['f1-score']:.2f}")
            found_weak = True
if not found_weak:
    print("   None — all gestures above 90% ✅")

# ─────────────────────────────────────────────
# STEP 7 — CONVERT AND SAVE AS TFLITE
# ─────────────────────────────────────────────
print(f"\n📦 Converting to TFLite...")

converter = tf.lite.TFLiteConverter.from_keras_model(model)

# Optimize for size and speed — important for real time inference
converter.optimizations = [tf.lite.Optimize.DEFAULT]

tflite_model = converter.convert()

with open(MODEL_FILE, 'wb') as f:
    f.write(tflite_model)

size_kb = len(tflite_model) / 1024
print(f"   Saved to: {MODEL_FILE}")
print(f"   Model size: {size_kb:.1f} KB")
print(f"\n✅ All done! Files saved:")
print(f"   {MODEL_FILE}")
print(f"   {LABEL_MAP_FILE}")