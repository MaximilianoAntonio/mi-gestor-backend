# GOPH/gestor_vehiculos/asignaciones/models.py
from django.db import models
from django.utils import timezone # Necesitarás esto si usas timezone.now como default

class Vehiculo(models.Model):
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('en_uso', 'En Uso'), # Ocupado en una asignación
        ('mantenimiento', 'Mantenimiento'),
        ('reservado', 'Reservado'), # Potencialmente asignado pero aún no en ruta
    ]
    TIPO_VEHICULO_CHOICES = [ # Podrías mover esto a su propio modelo si se vuelve complejo
        ('auto_funcionario', 'Auto para Funcionarios'),
        ('furgon_insumos', 'Furgón para Insumos'),
        ('ambulancia', 'Ambulancia para Pacientes'),
        ('camioneta_grande', 'Camioneta Grande Pasajeros'),
        ('camion_carga', 'Camión de Carga Ligera'),
        ('otro', 'Otro'),
    ]

    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    patente = models.CharField(max_length=20, unique=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='disponible')
    foto = models.ImageField(upload_to='vehiculos_fotos/', null=True, blank=True)

    # Nuevos campos para el algoritmo
    tipo_vehiculo = models.CharField(
        max_length=50,
        choices=TIPO_VEHICULO_CHOICES,
        default='auto_funcionario',
        help_text="Tipo de vehículo según su uso principal"
    )
    capacidad_pasajeros = models.PositiveIntegerField(
        default=4, # Renombrado desde 'capacidad' para mayor claridad
        help_text="Número máximo de pasajeros (sin incluir conductor)"
    )
    capacidad_carga_kg = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Capacidad de carga en kilogramos (si aplica)"
    )
    # Para características especiales (podría ser un campo JSON o ManyToMany a un modelo 'CaracteristicaVehiculo')
    caracteristicas_adicionales = models.TextField(
        blank=True, help_text="Características especiales: silla de ruedas, refrigerado, etc. (texto libre o JSON)"
    )
    # Ubicación (simplificado, para producción real podrías necesitar algo más robusto o integración GPS)
    ubicacion_actual_lat = models.FloatField(null=True, blank=True, help_text="Latitud actual del vehículo")
    ubicacion_actual_lon = models.FloatField(null=True, blank=True, help_text="Longitud actual del vehículo")
    # Si un vehículo tiene un conductor "principal" o "ligado" de forma preferente
    conductor_preferente = models.ForeignKey(
        'Conductor', # Usar string para evitar problemas de importación circular si Conductor se define después
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='vehiculos_preferentes',
        help_text="Conductor usual o preferente para este vehículo (opcional)"
    )


    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.patente})"

class Conductor(models.Model):
    ESTADO_DISPONIBILIDAD_CHOICES = [
        ('disponible', 'Disponible'),
        ('en_ruta', 'En Ruta'),
        ('descansando', 'Descansando'),
        ('no_disponible', 'No Disponible'),
    ]
    nombre = models.CharField(max_length=100, help_text="Nombre del conductor")
    apellido = models.CharField(max_length=100, help_text="Apellido del conductor")
    numero_licencia = models.CharField(max_length=50, unique=True, help_text="Número de licencia de conducir")
    fecha_vencimiento_licencia = models.DateField(help_text="Fecha de vencimiento de la licencia")
    telefono = models.CharField(max_length=20, blank=True, null=True, help_text="Número de teléfono (opcional)")
    email = models.EmailField(max_length=254, blank=True, null=True, help_text="Correo electrónico (opcional)")
    activo = models.BooleanField(default=True, help_text="Indica si el conductor está habilitado en el sistema")
    fecha_registro = models.DateTimeField(auto_now_add=True)

    # Nuevos campos
    tipos_vehiculo_habilitados = models.CharField( # Simplificado, podría ser ManyToManyField a TipoVehiculo
        max_length=255, blank=True,
        help_text="Tipos de vehículo que puede manejar (ej: auto_funcionario,furgon_insumos)"
    )
    estado_disponibilidad = models.CharField(
        max_length=20,
        choices=ESTADO_DISPONIBILIDAD_CHOICES,
        default='disponible'
    )
    # Ubicación (si los conductores inician desde una base o su casa)
    ubicacion_actual_lat = models.FloatField(null=True, blank=True, help_text="Latitud actual del conductor")
    ubicacion_actual_lon = models.FloatField(null=True, blank=True, help_text="Longitud actual del conductor")


    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.numero_licencia})"

    class Meta:
        verbose_name = "Conductor"
        verbose_name_plural = "Conductores"
        ordering = ['apellido', 'nombre']



class Asignacion(models.Model):
    ESTADO_ASIGNACION_CHOICES = [
        ('pendiente_auto', 'Pendiente de Asignación Automática'),
        ('programada', 'Programada (Auto/Manual)'),
        ('activa', 'Activa'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('fallo_auto', 'Falló Asignación Automática'), # Para revisión manual
    ]
    TIPO_SERVICIO_CHOICES = [
        ('funcionarios', 'Traslado de Funcionarios'),
        ('insumos', 'Traslado de Insumos'),
        ('pacientes', 'Traslado de Pacientes'),
        ('otro', 'Otro Servicio'),
    ]

    # Campos asignados (pueden ser null inicialmente si la asignación es automática)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.SET_NULL, null=True, blank=True, related_name='asignaciones_realizadas')
    conductor = models.ForeignKey(Conductor, on_delete=models.SET_NULL, null=True, blank=True, related_name='asignaciones_realizadas')

    # Información del servicio/ruta
    tipo_servicio = models.CharField(
        max_length=50,
        choices=TIPO_SERVICIO_CHOICES,
        default='otro'  # <--- AÑADIDO DEFAULT
    )
    destino_descripcion = models.CharField(
        max_length=200,
        help_text="Descripción del destino",
        default='Destino pendiente' # <--- DEFAULT YA ESTABA EN TU ARCHIVO
    )
    origen_descripcion = models.CharField(max_length=200, blank=True, help_text="Descripción del origen (opcional)")
    fecha_hora_solicitud = models.DateTimeField(
        auto_now_add=True, 
        help_text="Cuándo se creó la solicitud"
    )    
    fecha_hora_requerida_inicio = models.DateTimeField(
        help_text="Cuándo se necesita el servicio",
        default=timezone.now 
    )
    
    # Requerimientos para el algoritmo
    req_pasajeros = models.PositiveIntegerField(default=1, help_text="Número de pasajeros a trasladar")
    req_carga_kg = models.PositiveIntegerField(null=True, blank=True, help_text="Carga estimada en kg")
    req_tipo_vehiculo_preferente = models.CharField(
        max_length=50, choices=Vehiculo.TIPO_VEHICULO_CHOICES, blank=True, null=True,
        help_text="Tipo de vehículo preferido/requerido (opcional)"
    )
    req_caracteristicas_especiales = models.TextField(
        blank=True, help_text="Requerimientos especiales para el vehículo (ej: silla de ruedas)"
    )
    # Para el cálculo de distancia (coordenadas)
    origen_lat = models.FloatField(null=True, blank=True)
    origen_lon = models.FloatField(null=True, blank=True)
    destino_lat = models.FloatField(null=True, blank=True)
    destino_lon = models.FloatField(null=True, blank=True)

    # Campos de la asignación original
    fecha_hora_fin_prevista = models.DateTimeField(null=True, blank=True) # Puede calcularse o definirse después
    fecha_hora_fin_real = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_ASIGNACION_CHOICES, default='pendiente_auto')
    observaciones = models.TextField(blank=True, null=True)


    def __str__(self):
        conductor_str = f"{self.conductor.nombre} {self.conductor.apellido}" if self.conductor else "Por asignar"
        vehiculo_str = str(self.vehiculo) if self.vehiculo else "Por asignar"
        # Corregido para usar get_tipo_servicio_display() si existe o el valor directo
        tipo_servicio_display = self.get_tipo_servicio_display() if hasattr(self, 'get_tipo_servicio_display') else self.tipo_servicio
        return f"Servicio {tipo_servicio_display} a {self.destino_descripcion} - Vehículo: {vehiculo_str}, Conductor: {conductor_str}"