# GOPH/gestor_vehiculos/asignaciones/serializers.py
from rest_framework import serializers
from .models import Vehiculo, Conductor, Asignacion

class VehiculoSerializer(serializers.ModelSerializer):
    foto_url = serializers.ImageField(source='foto', read_only=True)

    class Meta:
        model = Vehiculo
        fields = [
            'id',
            'marca',
            'modelo',
            'patente',
            'capacidad_pasajeros', # CORREGIDO
            'estado',
            'foto',
            'foto_url',
            # Nuevos campos que podrías querer exponer:
            'tipo_vehiculo',
            'capacidad_carga_kg',
            'caracteristicas_adicionales',
            'ubicacion_actual_lat',
            'ubicacion_actual_lon',
            'conductor_preferente',
        ]
        extra_kwargs = {
            'foto': {'write_only': True, 'required': False}
        }
        # profundidad para mostrar detalles del conductor_preferente si es necesario
        # depth = 1


class ConductorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conductor
        fields = [
            'id',
            'nombre',
            'apellido',
            'numero_licencia',
            'fecha_vencimiento_licencia',
            'telefono',
            'email',
            'activo',
            'fecha_registro',
            # Nuevos campos que podrías querer exponer:
            'tipos_vehiculo_habilitados',
            'estado_disponibilidad',
            'ubicacion_actual_lat',
            'ubicacion_actual_lon',
        ]
        read_only_fields = ['fecha_registro']


class AsignacionSerializer(serializers.ModelSerializer):
    vehiculo = VehiculoSerializer(read_only=True)
    conductor = ConductorSerializer(read_only=True)

    vehiculo_id = serializers.PrimaryKeyRelatedField(
        queryset=Vehiculo.objects.all(),
        source='vehiculo',
        write_only=True,
        allow_null=True, # Permitir nulo si la asignación es automática
        required=False
    )
    conductor_id = serializers.PrimaryKeyRelatedField(
        queryset=Conductor.objects.filter(activo=True),
        source='conductor',
        write_only=True,
        allow_null=True, # Permitir nulo si la asignación es automática
        required=False
    )

    class Meta:
        model = Asignacion
        fields = [
            'id',
            'vehiculo',
            'vehiculo_id',
            'conductor',
            'conductor_id',
            'fecha_hora_requerida_inicio', # CORREGIDO
            'fecha_hora_fin_prevista',
            'fecha_hora_fin_real',
            'estado',
            'destino_descripcion', # CORREGIDO
            # Nuevos campos que podrías querer exponer:
            'tipo_servicio',
            'origen_descripcion',
            'fecha_hora_solicitud',
            'req_pasajeros',
            'req_carga_kg',
            'req_tipo_vehiculo_preferente',
            'req_caracteristicas_especiales',
            'origen_lat',
            'origen_lon',
            'destino_lat',
            'destino_lon',
            'observaciones',
        ]
        read_only_fields = ['fecha_hora_solicitud']


    def validate(self, data):
        # Obtener fechas del payload 'data' o del 'self.instance' si es una actualización y no están en 'data'
        fecha_inicio = data.get('fecha_hora_requerida_inicio', getattr(self.instance, 'fecha_hora_requerida_inicio', None))
        fecha_fin_prevista = data.get('fecha_hora_fin_prevista', getattr(self.instance, 'fecha_hora_fin_prevista', None))

        if fecha_inicio and fecha_fin_prevista:
            if fecha_inicio >= fecha_fin_prevista:
                raise serializers.ValidationError({
                    "fecha_hora_fin_prevista": "La fecha de fin prevista debe ser posterior a la fecha de inicio requerida."
                })
        
        # Validación de disponibilidad del vehículo
        # Usamos .get('vehiculo') que es el source de 'vehiculo_id' en el serializer.
        # El objeto vehiculo es establecido por DRF cuando se valida vehiculo_id.
        vehiculo_obj = data.get('vehiculo')

        if self.instance is None: # Creación (POST)
            if vehiculo_obj and vehiculo_obj.estado not in ['disponible', 'reservado']: # Permitir 'reservado' si la lógica lo maneja
                 raise serializers.ValidationError({
                     "vehiculo_id": f"El vehículo {vehiculo_obj.patente} no está disponible para una nueva asignación."
                 })
        elif 'vehiculo' in data and self.instance.vehiculo != vehiculo_obj: # Actualización (PUT/PATCH) y se cambia el vehículo
            if vehiculo_obj and vehiculo_obj.estado not in ['disponible', 'reservado']:
                 raise serializers.ValidationError({
                     "vehiculo_id": f"El nuevo vehículo {vehiculo_obj.patente} no está disponible."
                 })
        return data