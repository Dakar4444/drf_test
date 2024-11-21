from rest_framework import serializers
from .models import Link, Collection


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = '__all__'


class CollectionSerializer(serializers.ModelSerializer):
    links = serializers.PrimaryKeyRelatedField(
        queryset=Link.objects.all(), many=True, required=False
    )

    class Meta:
        model = Collection
        fields = ['id', 'name', 'description', 'links', 'created_at', 'updated_at']

    def create(self, validated_data):
        links = validated_data.pop('links', [])
        user = self.context['request'].user
        collection = Collection.objects.create(user=user, **validated_data)
        collection.links.set(links)
        return collection