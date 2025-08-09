document.addEventListener('DOMContentLoaded', function () {

    // Select all forms on the page
    const allForms = document.querySelectorAll('form');
    let targetForm = null;

    // Iterate through all forms to find the one containing 'upload_image'
    allForms.forEach(function (currentForm) {
        if (currentForm.querySelector('input[name="upload_image"]')) {
            targetForm = currentForm;
        }
    });

    // Select the 'upload_image' input
    const imageInput = document.querySelector('input[name="upload_image"]');

    if (!targetForm) {
        console.error('Form not found!');
    }
    if (!imageInput) {
        console.error('Image input field not found!');
    }

    // Add "Temizle" button next to the upload_image input
    if (imageInput) {
        const clearButton = document.createElement('button');
        clearButton.type = 'button';
        clearButton.textContent = 'Temizle';
        clearButton.style.marginLeft = '5px';
        clearButton.style.padding = '6px 12px';
        clearButton.style.backgroundColor = 'var(--button-hover-bg)';
        clearButton.style.color = 'white';
        clearButton.style.border = 'none';
        clearButton.style.borderRadius = '4px';
        clearButton.style.cursor = 'pointer';

        clearButton.addEventListener('click', function () {
            imageInput.value = ''; // Clear the selected image input
        });

        imageInput.parentNode.insertBefore(clearButton, imageInput.nextSibling);
    }

    // Create the custom modal for confirmation
    const modalOverlay = document.createElement('div');
    modalOverlay.setAttribute('id', 'custom-modal-overlay');
    modalOverlay.style.cssText = `
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-color: rgba(0, 0, 0, 0.5); z-index: 998;
        display: none;
    `;

    const modalContent = document.createElement('div');
    modalContent.setAttribute('id', 'custom-modal-content');
    modalContent.style.cssText = `
        position: fixed;
        top: 50%; left: 50%; transform: translate(-50%, -50%);
        width: 300px; padding: 20px;
        background-color: #3544e7; border-radius: 8px;
        box-shadow: 0 0 15px rgba(0, 0, 0, 0.2); z-index: 999;
        text-align: center; display: none;
    `;

    modalContent.innerHTML = `
        <p>Yeni bir görsel yüklenecek ve mevcut olan ile değiştirilecek. Eski görselin linkini kayıt etmediyseniz kaybolacaktır. Devam etmek istiyor musunuz?</p>
        <button id="modal-confirm" style="
            margin: 10px; padding: 10px 20px;
            background-color: #4CAF50; color: white; border: none;
            border-radius: 4px; cursor: not-allowed;" disabled>
            Evet (2)
        </button>
        <button id="modal-cancel" style="
            margin: 10px; padding: 10px 20px;
            background-color: #f44336; color: white; border: none;
            border-radius: 4px; cursor: pointer;">
            Hayır
        </button>
    `;

    document.body.appendChild(modalOverlay);
    document.body.appendChild(modalContent);

    const modalConfirmButton = document.getElementById('modal-confirm');
    const modalCancelButton = document.getElementById('modal-cancel');

    const showModal = () => {
        modalOverlay.style.display = 'block';
        modalContent.style.display = 'block';

        let countdown = 3;
        modalConfirmButton.textContent = `Evet (${countdown})`;

        const countdownInterval = setInterval(() => {
            countdown -= 1;
            modalConfirmButton.textContent = `Evet (${countdown})`;

            if (countdown <= 0) {
                clearInterval(countdownInterval);
                modalConfirmButton.disabled = false;
                modalConfirmButton.style.cursor = 'pointer';
                modalConfirmButton.textContent = 'Evet';
            }
        }, 1000);
    };

    const hideModal = () => {
        modalOverlay.style.display = 'none';
        modalContent.style.display = 'none';
        modalConfirmButton.disabled = true;
        modalConfirmButton.style.cursor = 'not-allowed';
    };

    if (targetForm && imageInput) {
        targetForm.addEventListener('submit', function (event) {
            if (imageInput.files.length > 0) {
                event.preventDefault();
                showModal();
            }
        });

        modalConfirmButton.onclick = function () {
            hideModal();
            targetForm.submit();
        };

        modalCancelButton.onclick = function () {
            hideModal();
        };
    }
});
