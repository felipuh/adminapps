import Swal from 'sweetalert2';

const baseOptions = {
  background: '#0f172a',
  color: '#e2e8f0',
  confirmButtonColor: '#004990',
  cancelButtonColor: '#475569',
  buttonsStyling: false,
  customClass: {
    popup: 'smart3ai-swal-popup',
    confirmButton: 'smart3ai-swal-confirm',
    cancelButton: 'smart3ai-swal-cancel',
  },
};

export async function showAlert({ title, text, icon = 'info', confirmButtonText }) {
  return Swal.fire({
    ...baseOptions,
    title,
    text,
    icon,
    confirmButtonText,
  });
}

export async function showConfirm({
  title,
  text,
  icon = 'warning',
  confirmButtonText,
  cancelButtonText,
}) {
  const result = await Swal.fire({
    ...baseOptions,
    title,
    text,
    icon,
    showCancelButton: true,
    confirmButtonText,
    cancelButtonText,
    reverseButtons: true,
    focusCancel: true,
  });

  return Boolean(result.isConfirmed);
}
