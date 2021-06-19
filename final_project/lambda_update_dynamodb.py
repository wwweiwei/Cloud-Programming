import json
import boto3 as boto

TOPIC_ARN = 'my-arn'
iot_kwargs = dict(thingName='final', shadowName='purchase_info')

def lambda_handler(event, context):
    print('Lambda triggered')

    # Get purchase information
    iot = boto.client('iot-data')
    body = iot.get_thing_shadow(**iot_kwargs)
    payload = json.load(body['payload'])
    state = payload['state']['desired']
    timestamp = payload['metadata']['desired']['item_id']['timestamp']
    user_id, item_id, count = state['user_id'], state['item_id'], state['count']
    print((
        f'timestamp: {timestamp}, user_id: {user_id}, '
        f'item_id: {item_id}, count: {count}'
    ))

    # Update databases
    ddb = boto.client('dynamodb')

    if user_id != 'null':
        user_item = {
            'timestamp': {'N': str(timestamp)},
            'item_id': {'S': item_id},
            'count': {'N': str(count)},
            'isPay': {'BOOL': False}
        }
        ddb.put_item(TableName=user_id, Item=user_item)
        print(f'User table {user_id} updated')

        item_item = {
            'timestamp': {'N': str(timestamp)},
            'count': {'N': str(count)}
        }
        ddb.put_item(TableName=item_id, Item=item_item)
        print(f'Item table {item_id} updated')

    ddb.update_item(
        TableName='stock',
        Key={'item_id': {'S': item_id}},
        UpdateExpression='SET stock = stock - :delta',
        ExpressionAttributeValues={':delta': {'N': str(count)}}
    )
    print(f'Stock table item {item_id} updated')

    response = ddb.get_item(TableName='stock', Key={'item_id': {'S': item_id}})
    if response['Item']['stock']['N'] == '0':
        sns = boto.client('sns')
        msg = f'Item {item_id} is out of stock, please replenish the stock.'
        sns.publish(TopicArn=TOPIC_ARN, Message=msg)
        print('Invoked out-of-stock alarm.')

    return "Test succeeded"
