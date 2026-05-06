python detect_labels.py \
    --input-dir corpus/deduplicated_2 \
    --output-dir corpus/02_labelled \
    --max-results 150 \
    --workers 4 \
    #--test 20 \
    #--force

# EC2 instance
nohup bash run_python_ec2.sh detect_labels.py --input-dir corpus/deduplicated_2 --output-dir corpus/02_labelled --max-results 150 --workers 4 > process_output.log 2>&1 &

python label_types.py \
    --input-dir corpus/02_labelled \
    --output-dir corpus/03_label_types

