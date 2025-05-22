# asignaciones/admin.py
from django.contrib import admin
from .models import Vehiculo, Conductor, Asignacion
from django.utils.html import format_html

@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = (
        'patente',
        'marca',
        'modelo',
        'estado',
        'tipo_vehiculo', # Añadido para ver el tipo
        'capacidad_pasajeros', # CORREGIDO: antes 'capacidad'
        'ver_foto'
    )
    list_filter = (
        'estado',
        'marca',
        'tipo_vehiculo', # Añadido para filtrar
        'capacidad_pasajeros' # CORREGIDO: antes 'capacidad'
    )
    search_fields = ('patente', 'marca', 'modelo')
    list_editable = ('estado',)
    readonly_fields = ('foto_preview',)

    fieldsets = (
        (None, {
            'fields': ('patente', 'marca', 'modelo', 'tipo_vehiculo')
        }),
        ('Capacidad y Características', {
            'fields': ('capacidad_pasajeros', 'capacidad_carga_kg', 'caracteristicas_adicionales')
        }),
        ('Estado y Multimedia', {
            'fields': ('estado', 'foto', 'foto_preview')
        }),
        ('Ubicación y Conductor Preferente', { # Nuevo
            'fields': ('ubicacion_actual_lat', 'ubicacion_actual_lon', 'conductor_preferente')
        }),
    )
    autocomplete_fields = ['conductor_preferente']


    def ver_foto(self, obj):
        if obj.foto:
            return format_html('<img src="{}" width="50" height="50" />', obj.foto.url)
        return "Sin foto"
    ver_foto.short_description = 'Foto'

    def foto_preview(self, obj):
        if obj.foto:
            return format_html('<img src="{}" width="150" height="150" />', obj.foto.url)
        return "(Sin imagen)"
    foto_preview.short_description = 'Vista Previa de Foto'


@admin.register(Conductor)
class ConductorAdmin(admin.ModelAdmin):
    list_display = (
        'apellido',
        'nombre',
        'numero_licencia',
        'fecha_vencimiento_licencia',
        'activo',
        'estado_disponibilidad' # Añadido
    )
    list_filter = ('activo', 'estado_disponibilidad', 'fecha_vencimiento_licencia') # Añadido 'estado_disponibilidad'
    search_fields = ('nombre', 'apellido', 'numero_licencia')
    list_editable = ('activo', 'estado_disponibilidad') # Añadido 'estado_disponibilidad'
    ordering = ('apellido', 'nombre')
    
    fieldsets = (
        (None, {
            'fields': ('nombre', 'apellido', 'numero_licencia', 'fecha_vencimiento_licencia')
        }),
        ('Contacto y Estado', {
            'fields': ('telefono', 'email', 'activo', 'estado_disponibilidad', 'tipos_vehiculo_habilitados')
        }),
         ('Ubicación Actual', { # Nuevo
            'fields': ('ubicacion_actual_lat', 'ubicacion_actual_lon')
        }),
    )


@admin.register(Asignacion)
class AsignacionAdmin(admin.ModelAdmin):
    list_display = (
        'id', # Es bueno tener el ID visible
        'vehiculo',
        'conductor',
        'destino_descripcion',         # CORREGIDO: antes 'destino'
        'tipo_servicio',               # Añadido
        'fecha_hora_requerida_inicio', # CORREGIDO: antes 'fecha_hora_inicio'
        'estado'
    )
    list_filter = (
        'estado',
        'tipo_servicio',                # Añadido
        'fecha_hora_requerida_inicio',  # CORREGIDO: antes 'fecha_hora_inicio'
        'vehiculo',
        'conductor'
    )
    search_fields = (
        'id',
        'destino_descripcion',
        'vehiculo__patente',
        'conductor__nombre',
        'conductor__apellido'
    )
    autocomplete_fields = ['vehiculo', 'conductor']
    list_editable = ('estado',) # Puedes hacer el estado editable si quieres
    ordering = ('-fecha_hora_requerida_inicio',)


    fieldsets = (
        ('Solicitud de Servicio', {
            'fields': ('tipo_servicio', 'origen_descripcion', 'destino_descripcion', 'fecha_hora_requerida_inicio')
        }),
        ('Requerimientos Específicos', {
            'classes': ('collapse',), # Para que aparezca colapsado por defecto
            'fields': ('req_pasajeros', 'req_carga_kg', 'req_tipo_vehiculo_preferente', 'req_caracteristicas_especiales',
                       'origen_lat', 'origen_lon', 'destino_lat', 'destino_lon')
        }),
        ('Asignación (Vehículo/Conductor)', {
            'fields': ('vehiculo', 'conductor')
        }),
        ('Estado y Seguimiento', {
            'fields': ('estado', 'fecha_hora_fin_prevista', 'fecha_hora_fin_real', 'observaciones', 'fecha_hora_solicitud')
        }),
    )
    readonly_fields = ('fecha_hora_solicitud',) # La fecha de solicitud se pone automáticamente

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('vehiculo', 'conductor')