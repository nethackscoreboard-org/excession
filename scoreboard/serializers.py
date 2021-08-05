from rest_framework import serializers
from .models import GameRecord
import itertools

STANDARD_SCOREBOARD_FIELDS_GAME = [
    'srv', 'var', 'ver', 'name', 'character', 'points', 'turns', 'duration', 'dlvl', 'HP', 'time', 'death_reason'
]

STANDARD_SCOREBOARD_FIELDS_ASCENSION = [
    'srv', 'var', 'ver', 'name', 'character', 'points', 'turns', 'duration', 'dlvl', 'HP', 'time', 'win_type', 'conducts'
]

class ConductListField(serializers.RelatedField):
    def to_representation(self, value):
        return value.short_name

class AchievementListField(serializers.RelatedField):
    def to_representation(self, value):
        return value.title

class AscensionSerializer(serializers.ModelSerializer):
    srv = serializers.CharField(source='server', max_length=128)
    var = serializers.CharField(source='variant', max_length=128)
    ver = serializers.CharField(source='version', max_length=128)
    character = serializers.SerializerMethodField()
    dlvl = serializers.SerializerMethodField()
    HP = serializers.SerializerMethodField()
    conducts = ConductListField(many=True, read_only=True)
    time = serializers.DateTimeField(source='endtime', format='%Y-%m-%d %H:%M')
    duration = serializers.DurationField(source='realtime')
    win_type = serializers.CharField(source='death', max_length=1024)

    class Meta:
        model = GameRecord
        fields = STANDARD_SCOREBOARD_FIELDS_ASCENSION
    
    def get_character(self, obj):
        return "-".join(itertools.filterfalse(lambda x: not x, [obj.role, obj.race, obj.gender, obj.align]))
        
    def get_dlvl(self, obj):
        if obj.maxlvl:
            return "/{}".format(obj.maxlvl)
        else:
            return ""
        
    def get_HP(self, obj):
        if obj.hp and obj.maxhp:
            return "{}/{}".format(obj.hp, obj.maxhp)
        elif obj.hp:
            return obj.hp
        else:
            return ""

class GameRecordSerializer(serializers.ModelSerializer):
    srv = serializers.CharField(source='server', max_length=128)
    var = serializers.CharField(source='variant', max_length=128)
    ver = serializers.CharField(source='version', max_length=128)
    character = serializers.SerializerMethodField()
    dlvl = serializers.SerializerMethodField()
    HP = serializers.SerializerMethodField()
    time = serializers.DateTimeField(source='endtime', format='%Y-%m-%d %H:%M')
    duration = serializers.DurationField(source='realtime')
    death_reason = serializers.CharField(source='death', max_length=1024)

    class Meta:
        model = GameRecord
        fields = STANDARD_SCOREBOARD_FIELDS_GAME
    
    def get_character(self, obj):
        return "-".join(itertools.filterfalse(lambda x: not x, [obj.role, obj.race, obj.gender, obj.align]))
        
    def get_dlvl(self, obj):
        if obj.deathlev and obj.maxlvl:
            return "{}/{}".format(obj.deathlev, obj.maxlvl)
        elif obj.deathlev:
            return obj.deathlev
        else:
            return ""
        
    def get_HP(self, obj):
        if obj.hp and obj.maxhp:
            return "{}/{}".format(obj.hp, obj.maxhp)
        elif obj.hp:
            return obj.hp
        else:
            return ""

class XlogRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameRecord
        fields = '__all__'
    
    def create(self, validated_data):
        return GameRecord.create(**validated_data)
