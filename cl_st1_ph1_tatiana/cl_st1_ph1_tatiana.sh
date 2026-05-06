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

python top_labels.py \
    --input-dir corpus/03_label_types \
    --output-dir corpus/04_top_labels

rm -rf columns columns_clean
python columns.py
# Output: columns, columns_clean, file_ids.txt, index_top_labels.txt

python merge_columns.py
# Output: sas/counts.txt

