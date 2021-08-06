from rest_framework.parsers import BaseParser
from rest_framework import serializers
from datetime import date, datetime, timedelta, timezone
from .models import GameRecord
import re

required_xlog_fields = [
    'version',
    'name',
    'death',
    'turns',
    'role',
    'starttime',
    'endtime',
]

class XlogParser(BaseParser):
    delimiter = '\t'
    separator = '='

    def __convert__(self, value):
        if re.match('^[0-9]+$', value) or re.match('^0x[0-9a-fA-F]+$', value):
            return int(value, 0)
        else:
            return value

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parse xlogfile data into python primitive types
        """
        return [
            {
                k: self.__convert__(v)
                for k, v in [
                    i.split(self.separator)
                    for i in line.rstrip().split(self.delimiter)
                ]
            }
            for line in stream.readlines()
        ]

class TimeStampField(serializers.DateTimeField):
    def to_representation(self, value):
        return int(value.timestamp())
    
    def to_internal_value(self, value):
        return datetime.fromtimestamp(value, timezone.utc)

class XlogListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        games = [GameRecord(**item) for item in validated_data]
        return GameRecord.objects.bulk_create(games)

class XlogRecordSerializer(serializers.ModelSerializer):
    starttime = TimeStampField()
    endtime = TimeStampField()
    server = serializers.SerializerMethodField()
    variant = serializers.SerializerMethodField()
    wallclock = serializers.SerializerMethodField()

    class Meta:
        model = GameRecord
        list_serializer_class = XlogListSerializer
        fields = '__all__'
    
    def create(self, validated_data):
        return GameRecord.create(**validated_data)
    
    def validate(self, data):
        for field in required_xlog_fields:
            if not field in data:
                raise serializers.ValidationError('missing required field')
        if data['endtime'] < data['starttime']:
            raise serializers.ValidationError('game cannot end before it has begun')
        if data['endtime'] - data['starttime'] < data['realtime']:
            raise serializers.ValidationError('wallclock time cannot be less than realtime')
        return data
    
    def validate_starttime(self, value):
        if value and value <= datetime.now(tz=timezone.utc):
            return value
        else:
            raise serializers.ValidationError('game cannot start in the future')

    def validate_endtime(self, value):
        if value and value <= datetime.now(tz=timezone.utc):
            return value
        else:
            raise serializers.ValidationError('game cannot end in the future')

    def get_wallclock(self, obj):
        return obj.endtime - obj.starttime
    
    def get_server(self, obj):
        return self.context['server']
    
    def get_variant(self, obj):
        return self.context['variant']