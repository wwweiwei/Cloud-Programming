import json
import boto3 as boto

src_bkt = 'bucket-name'
to_s3_payload = lambda bkt, name: {'S3Object': {'Bucket': bkt, 'Name': name}}
iot_kwargs = lambda s, t: dict(
    thingName='final',
    shadowName='auth_result',
    payload=json.dumps({'state': {'desired': {'user_led': s, 'user_id': t}}})
)


def lambda_handler(event, context):
    metadata = event['Records'][0]['s3']
    tgt_bkt, tgt_img = metadata['bucket']['name'], metadata['object']['key']
    print(f'bkt_name: {tgt_bkt}, tgt_name: {tgt_img}')

    # Get the list of source filenames from the order bucket
    order_bucket = boto.resource('s3').Bucket(src_bkt)
    order_obj = [obj.key for obj in order_bucket.objects.all()]

    # Iterate through order bucket to detect faces
    reko = boto.client('rekognition')
    iot = boto.client('iot-data')

    for src_img in order_obj:
        response = reko.compare_faces(
            SourceImage=to_s3_payload(src_bkt, src_img),
            TargetImage=to_s3_payload(tgt_bkt, tgt_img)
        )
        if len(response['FaceMatches']) > 0:
            user_id = src_img.split('.')[0]
            print(f'Match found: user_id {user_id}.')
            iot.update_thing_shadow(**iot_kwargs('pass', user_id))
            print('Switched user_led to "pass"')
            break
    else:
        iot.update_thing_shadow(**iot_kwargs('fail', None))
        print('Match not found. Switched user_led to "fail"')

    return "Test succeeded"
