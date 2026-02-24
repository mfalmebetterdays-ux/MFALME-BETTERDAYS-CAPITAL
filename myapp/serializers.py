from rest_framework import serializers
from .models import Package

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = [
            'id', 'name', 'description', 'price', 'package_type',
            'duration', 'is_recurring', 'popular', 'features', 'image',
            'status', 'sales_count'
        ]
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # Format features as list if they're a string
        if isinstance(data['features'], str):
            data['features'] = [f.strip() for f in data['features'].split('\n') if f.strip()]
        
        # Add banner field for frontend compatibility
        if instance.image:
            data['banner'] = instance.image.url
        else:
            data['banner'] = None
            
        # Format price
        data['price'] = float(instance.price)
        
        # Add type display
        data['type_display'] = instance.get_package_type_display()
        
        return data

class PackageCreateUpdateSerializer(serializers.ModelSerializer):
    features = serializers.CharField(write_only=True, required=False, 
                                   help_text="Enter features separated by new lines")
    
    class Meta:
        model = Package
        fields = '__all__'
    
    def validate_features(self, value):
        if value and isinstance(value, str):
            return [f.strip() for f in value.split('\n') if f.strip()]
        return value
    
    def create(self, validated_data):
        if 'features' in validated_data and isinstance(validated_data['features'], str):
            features = validated_data['features']
            validated_data['features'] = [f.strip() for f in features.split('\n') if f.strip()]
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'features' in validated_data and isinstance(validated_data['features'], str):
            features = validated_data['features']
            validated_data['features'] = [f.strip() for f in features.split('\n') if f.strip()]
        return super().update(instance, validated_data)