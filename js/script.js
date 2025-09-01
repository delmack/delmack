// Aguarda o carregamento completo da página
document.addEventListener('DOMContentLoaded', function() {
    // Remove a tela de loading após o carregamento
    setTimeout(function() {
        document.querySelector('.loading-screen').style.opacity = '0';
        setTimeout(function() {
            document.querySelector('.loading-screen').style.display = 'none';
        }, 500);
    }, 2000);

    // Animação de elementos ao rolar a página
    function animateOnScroll() {
        const elements = document.querySelectorAll('.couple-container, .location-container, .dresscode-content, .gift-options, .rsvp-container');
        
        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const screenPosition = window.innerHeight / 1.3;
            
            if (elementPosition < screenPosition) {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }
        });
    }

    // Inicializa as opacidades para a animação de scroll
    const animatedElements = document.querySelectorAll('.couple-container, .location-container, .dresscode-content, .gift-options, .rsvp-container');
    animatedElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
    });

    // Configura o evento de scroll
    window.addEventListener('scroll', animateOnScroll);
    // Executa uma vez ao carregar para verificar elementos já visíveis
    animateOnScroll();

    // Modal de PIX
    const giftButtons = document.querySelectorAll('.gift-btn');
    const modal = document.getElementById('pixModal');
    const closeModal = document.querySelector('.close-modal');
    const copyPixButton = document.querySelector('.copy-pix');

    giftButtons.forEach(button => {
        button.addEventListener('click', function() {
            const value = this.getAttribute('data-value');
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        });
    });

    closeModal.addEventListener('click', function() {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    });

    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });

    copyPixButton.addEventListener('click', function() {
        const pixKey = '41999445586';
        navigator.clipboard.writeText(pixKey).then(() => {
            copyPixButton.textContent = 'Chave copiada!';
            setTimeout(() => {
                copyPixButton.textContent = 'Copiar Chave PIX';
            }, 2000);
        });
    });

    // Formulário de confirmação de presença
    const rsvpForm = document.querySelector('.rsvp-form');
    rsvpForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Aqui você normalmente enviaria os dados para um servidor
        // Por enquanto, vamos apenas mostrar uma mensagem de sucesso
        alert('Obrigado por confirmar sua presença! Estamos ansiosos para vê-lo em nosso casamento.');
        rsvpForm.reset();
    });

    // Adiciona flores decorativas dinamicamente
    function addFloralDecorations() {
        const floralSvg = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <path d="M50,20 A30,30 0 1,1 50,80 A30,30 0 1,1 50,20" fill="none" stroke="#D4AF37" stroke-width="2"/>
            <path d="M50,30 A20,20 0 1,1 50,70 A20,20 0 1,1 50,30" fill="none" stroke="#D4AF37" stroke-width="2"/>
            <circle cx="50" cy="50" r="5" fill="#D4AF37"/>
        </svg>`;
        
        // Converter SVG para URL de dados para uso em background-image
        const floralDataUrl = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(floralSvg);
        
        // Aplicar às decorações florais
        const floralDecorations = document.querySelectorAll('.floral-decoration');
        floralDecorations.forEach(decoration => {
            decoration.style.backgroundImage = `url("${floralDataUrl}")`;
        });
    }

    addFloralDecorations();
});