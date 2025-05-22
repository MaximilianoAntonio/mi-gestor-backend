# GOPH/gestor_vehiculos/asignaciones/views.py
from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter


from .models import Vehiculo, Conductor, Asignacion
from .serializers import (
    VehiculoSerializer,
    ConductorSerializer,
    AsignacionSerializer
)

class VehiculoViewSet(viewsets.ModelViewSet):
    queryset = Vehiculo.objects.all().order_by('marca', 'modelo')
    serializer_class = VehiculoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'marca', 'tipo_vehiculo', 'capacidad_pasajeros'] # CORREGIDO: 'capacidad' a 'capacidad_pasajeros', añadido 'tipo_vehiculo'
    search_fields = ['patente', 'modelo', 'marca']
    ordering_fields = ['marca', 'modelo', 'capacidad_pasajeros', 'estado', 'tipo_vehiculo'] # CORREGIDO: 'capacidad' a 'capacidad_pasajeros', añadido 'tipo_vehiculo'

class ConductorViewSet(viewsets.ModelViewSet):
    queryset = Conductor.objects.all().order_by('apellido', 'nombre')
    serializer_class = ConductorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['activo', 'estado_disponibilidad'] # Añadido 'estado_disponibilidad'
    search_fields = ['nombre', 'apellido', 'numero_licencia']
    ordering_fields = ['apellido', 'nombre', 'activo', 'estado_disponibilidad'] # Añadido 'estado_disponibilidad'


class AsignacionViewSet(viewsets.ModelViewSet):
    queryset = Asignacion.objects.all().select_related('vehiculo', 'conductor').order_by('-fecha_hora_solicitud')
    serializer_class = AsignacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # Actualizado para los nuevos nombres y campos
    filterset_fields = {
        'estado': ['exact'],
        'tipo_servicio': ['exact'],
        'vehiculo__marca': ['exact', 'icontains'],
        'conductor__apellido': ['exact', 'icontains'],
        'fecha_hora_requerida_inicio': ['exact', 'gte', 'lte', 'date'], # Permite filtrar por fecha, mayor/menor que
    }
    search_fields = ['destino_descripcion', 'vehiculo__patente', 'observaciones'] # CORREGIDO: 'destino' a 'destino_descripcion'
    ordering_fields = ['fecha_hora_requerida_inicio', 'fecha_hora_fin_prevista', 'estado', 'tipo_servicio'] # CORREGIDO: 'fecha_hora_inicio' a 'fecha_hora_requerida_inicio'

    @action(detail=True, methods=['post'], url_path='completar')
    def completar_asignacion(self, request, pk=None):
        asignacion = self.get_object()
        if asignacion.estado == 'activa':
            asignacion.estado = 'completada'
            asignacion.fecha_hora_fin_real = timezone.now()
            if asignacion.vehiculo:
                asignacion.vehiculo.estado = 'disponible'
                asignacion.vehiculo.save()
            if asignacion.conductor: # Poner conductor como disponible también
                asignacion.conductor.estado_disponibilidad = 'disponible'
                asignacion.conductor.save()
            asignacion.save()
            return Response({'status': 'asignación completada', 'asignacion': self.get_serializer(asignacion).data}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'La asignación no está activa o ya está completada/cancelada.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='iniciar')
    def iniciar_asignacion(self, request, pk=None):
        asignacion = self.get_object()
        if asignacion.estado == 'programada':
            if not asignacion.vehiculo or not asignacion.conductor:
                return Response({'error': 'La asignación debe tener un vehículo y un conductor asignados para poder iniciarla.'}, status=status.HTTP_400_BAD_REQUEST)

            if asignacion.vehiculo.estado != 'disponible' and asignacion.vehiculo.estado != 'reservado': # Permitir iniciar si estaba reservado
                return Response({'error': f'El vehículo {asignacion.vehiculo.patente} no está disponible.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if asignacion.conductor.estado_disponibilidad != 'disponible' or not asignacion.conductor.activo :
                return Response({'error': f'El conductor {asignacion.conductor} no está disponible o no está activo.'}, status=status.HTTP_400_BAD_REQUEST)

            asignacion.vehiculo.estado = 'en_uso'
            asignacion.vehiculo.save()
            asignacion.conductor.estado_disponibilidad = 'en_ruta'
            asignacion.conductor.save()
            
            asignacion.estado = 'activa'
            asignacion.save()
            return Response({'status': 'asignación iniciada', 'asignacion': self.get_serializer(asignacion).data}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'La asignación no está programada o ya está en otro estado.'}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        # Aquí podrías llamar a tu futuro servicio de asignación automática si el estado es 'pendiente_auto'
        # asignacion_obj = serializer.save()
        # if asignacion_obj.estado == 'pendiente_auto':
        #     from .services import intentar_asignacion_automatica # Suponiendo que lo crearás
        #     intentar_asignacion_automatica(asignacion_obj)
        serializer.save()