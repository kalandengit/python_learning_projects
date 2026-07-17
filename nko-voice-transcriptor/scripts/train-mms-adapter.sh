#!/usr/bin/env bash
# Reproducible wrapper around Hugging Face's official MMS adapter trainer.
set -euo pipefail

DATASET_DIR="${1:?Usage: $0 DATASET_DIR OUTPUT_DIR [MODEL_ID]}"
OUTPUT_DIR="${2:?Usage: $0 DATASET_DIR OUTPUT_DIR [MODEL_ID]}"
MODEL_ID="${3:-facebook/mms-1b-all}"
TRANSFORMERS_REF="${TRANSFORMERS_REF:-v4.57.1}"
TRAINER="${OUTPUT_DIR}/run_speech_recognition_ctc_adapter.py"

command -v nvidia-smi >/dev/null || {
  echo "A CUDA-capable training machine is strongly recommended." >&2
  exit 2
}
[ -f "${DATASET_DIR}/train/metadata.csv" ] || {
  echo "Missing ${DATASET_DIR}/train/metadata.csv" >&2
  exit 2
}
[ -f "${DATASET_DIR}/test/metadata.csv" ] || {
  echo "Missing ${DATASET_DIR}/test/metadata.csv" >&2
  exit 2
}

mkdir -p "$OUTPUT_DIR"
python3 -m pip install --upgrade \
  "torch>=2.2" "transformers[torch]==4.57.1" "datasets[audio]>=3" \
  "accelerate>=1" "evaluate>=0.4" "jiwer>=3" soundfile
curl -fsSL \
  "https://raw.githubusercontent.com/huggingface/transformers/${TRANSFORMERS_REF}/examples/pytorch/speech-recognition/run_speech_recognition_ctc_adapter.py" \
  -o "$TRAINER"

python3 "$TRAINER" \
  --dataset_name audiofolder \
  --data_dir "$DATASET_DIR" \
  --model_name_or_path "$MODEL_ID" \
  --output_dir "$OUTPUT_DIR" \
  --target_language bam \
  --audio_column_name audio \
  --text_column_name transcription \
  --num_train_epochs 10 \
  --per_device_train_batch_size 4 \
  --gradient_accumulation_steps 4 \
  --learning_rate 1e-3 \
  --warmup_steps 100 \
  --eval_strategy steps \
  --eval_steps 100 \
  --save_steps 100 \
  --save_total_limit 3 \
  --gradient_checkpointing \
  --fp16 \
  --do_train --do_eval

printf '%s\n' "Model adapter written to $OUTPUT_DIR"
