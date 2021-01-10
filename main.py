#!/usr/bin/env python3

import os
import re
import discord
import boto3
import botocore

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = '/caretaker'
RE_MATCH = rf'^\{COMMAND_PREFIX}\s(\w+)(?:\s(\w+))?$'
USAGE = f"""Usage: `{COMMAND_PREFIX} verb [ec2-instance-name]`
Example: `{COMMAND_PREFIX} status`"""


def validate_command(command):
    return bool(re.match(RE_MATCH, command))


def parse_args(command):
    re_groups = re.match(RE_MATCH, command)
    return [re_groups[1], re_groups[2]]


def ec2_action(verb, instance=None):
    response = {}
    ec2 = boto3.resource('ec2')
    if verb != 'status':
        filter = [{
            'Name':'tag:Name', 
            'Values': [instance]
        }]
    else:
        filter = []
    for instance in ec2.instances.filter(Filters=filter):
        for tag in instance.tags:
            if tag['Key'] == 'Name':
                instance_tag_name = tag['Value']
                break
        response[instance_tag_name] = {
            'address': instance.public_dns_name,
            'last_start': str(instance.launch_time),
            'status': instance.state['Name']
        }
        try:
            if verb == 'start':
                response = instance.start()
            elif verb == 'stop':
                response = instance.stop()
        except botocore.exceptions.ParamValidationError:
            return USAGE
    return response


client = discord.Client()


@client.event
async def on_message(message):
    if message.author.id == client.user.id:
        return
    if not message.content.startswith(COMMAND_PREFIX):
        return
    elif not validate_command(message.content):
        await message.reply(
            USAGE,
            mention_author=True
        )
    else:
        args_parsed = parse_args(message.content)
        await message.reply(
            ec2_action(args_parsed[0], args_parsed[1]),
            mention_author=True
        )


client.run(DISCORD_TOKEN)
