import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Building2, Mail, Phone, Globe, MapPin, AlertCircle } from 'lucide-react';
import { organizationService } from '../services/api';
import toast from 'react-hot-toast';

const CreateOrganizationPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    legal_name: '',
    email: '',
    phone: '',
    website: '',
    address: '',
    city: '',
    state: '',
    country: '',
    industry: '',
    size: '',
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    // Validación básica
    if (!formData.name || !formData.code) {
      setError('El nombre y código de la organización son requeridos');
      return;
    }

    setLoading(true);
    try {
      const result = await organizationService.create(formData);
      toast.success('Organización creada exitosamente');
      navigate(`/organizations/${result.id}`);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 
                          err.response?.data?.non_field_errors?.[0] ||
                          'Error al crear la organización';
      setError(errorMessage);
      console.error('Error creando organización:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    navigate('/organizations');
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={handleCancel}
          className="p-2 hover:bg-dark-400/50 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-gray-400" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-white">Nueva Organización</h1>
          <p className="text-gray-400">Crear una nueva organización cliente</p>
        </div>
      </div>

      {/* Form Card */}
      <div className="glass-card p-6">
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-3 text-red-400">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Row 1: Code & Name */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Código <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                name="code"
                value={formData.code}
                onChange={handleInputChange}
                placeholder="ORG00001"
                className="glass-input"
                disabled={loading}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Nombre <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="Nombre comercial"
                className="glass-input"
                disabled={loading}
                required
              />
            </div>
          </div>

          {/* Row 2: Legal Name */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Razón Social
            </label>
            <input
              type="text"
              name="legal_name"
              value={formData.legal_name}
              onChange={handleInputChange}
              placeholder="Nombre legal completo"
              className="glass-input"
              disabled={loading}
            />
          </div>

          {/* Row 3: Email & Phone */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center gap-2">
                <Mail size={18} />
                Email
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="contacto@ejemplo.com"
                className="glass-input"
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center gap-2">
                <Phone size={18} />
                Teléfono
              </label>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleInputChange}
                placeholder="+52 55 1234 5678"
                className="glass-input"
                disabled={loading}
              />
            </div>
          </div>

          {/* Row 4: Website */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center gap-2">
              <Globe size={18} />
              Sitio Web
            </label>
            <input
              type="url"
              name="website"
              value={formData.website}
              onChange={handleInputChange}
              placeholder="https://ejemplo.com"
              className="glass-input"
              disabled={loading}
            />
          </div>

          {/* Row 5: Address */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center gap-2">
              <MapPin size={18} />
              Dirección
            </label>
            <input
              type="text"
              name="address"
              value={formData.address}
              onChange={handleInputChange}
              placeholder="Calle, número, departamento"
              className="glass-input"
              disabled={loading}
            />
          </div>

          {/* Row 6: City, State, Country */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Ciudad
              </label>
              <input
                type="text"
                name="city"
                value={formData.city}
                onChange={handleInputChange}
                placeholder="Ciudad de México"
                className="glass-input"
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Estado
              </label>
              <input
                type="text"
                name="state"
                value={formData.state}
                onChange={handleInputChange}
                placeholder="CDMX"
                className="glass-input"
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                País
              </label>
              <input
                type="text"
                name="country"
                value={formData.country}
                onChange={handleInputChange}
                placeholder="México"
                className="glass-input"
                disabled={loading}
              />
            </div>
          </div>

          {/* Row 7: Industry & Size */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Industria
              </label>
              <select
                name="industry"
                value={formData.industry}
                onChange={handleInputChange}
                className="glass-input"
                disabled={loading}
              >
                <option value="">Seleccionar industria</option>
                <option value="manufacturing">Manufactura</option>
                <option value="services">Servicios</option>
                <option value="technology">Tecnología</option>
                <option value="retail">Retail</option>
                <option value="healthcare">Salud</option>
                <option value="other">Otros</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Tamaño
              </label>
              <select
                name="size"
                value={formData.size}
                onChange={handleInputChange}
                className="glass-input"
                disabled={loading}
              >
                <option value="">Seleccionar tamaño</option>
                <option value="micro">Micro (1-9)</option>
                <option value="small">Pequeña (10-49)</option>
                <option value="medium">Mediana (50-249)</option>
                <option value="large">Grande (250+)</option>
              </select>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t border-gray-700/30">
            <button
              type="button"
              onClick={handleCancel}
              className="flex-1 glass-button-secondary"
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="flex-1 glass-button flex items-center justify-center gap-2"
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
                  Creando...
                </>
              ) : (
                <>
                  <Building2 size={18} />
                  Crear Organización
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateOrganizationPage;
