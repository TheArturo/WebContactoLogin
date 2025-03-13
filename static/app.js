document.addEventListener("DOMContentLoaded", function () {
    // Botón tipo hamburguesa para dispositivos móviles
    const burger = document.querySelector(".burger");
    const navLinks = document.querySelector(".nav-links");

    if (burger && navLinks) {
        burger.addEventListener("click", () => {
            navLinks.classList.toggle("active");
        });
    }

    // Mostrar/Ocultar contraseña
    const togglePassword = document.getElementById("togglePassword");
    const passwordField = document.getElementById("password");

    if (togglePassword && passwordField) {
        togglePassword.addEventListener("click", function () {
            const isPasswordHidden = passwordField.type === "password";
            passwordField.type = isPasswordHidden ? "text" : "password";
            this.classList.toggle("active", isPasswordHidden);
        });
    }

    // Manejo del formulario de contacto
    const contactForm = document.getElementById("contact-form");

    if (contactForm) {
        contactForm.addEventListener("submit", function (event) {
            event.preventDefault(); 

            const submitButton = this.querySelector('button[type="submit"]');
            submitButton.classList.add("loading");

            const formData = new FormData(this);

            fetch("/send_email", {
                method: "POST",
                body: formData
            })
            .then(response => response.text())  // 📌 Leer la respuesta de Flask
            .then(data => {
                if (data === "success") {
                    showFlashMessage("Mensaje enviado correctamente.", "success");
                    contactForm.reset(); // 📌 Limpia el formulario si se envió bien
                } else {
                    showFlashMessage("Hubo un error al enviar el mensaje.", "danger");
                }
            })
            .catch(error => {
                console.error("Error:", error);
                showFlashMessage("Hubo un error al enviar el mensaje.", "danger");
            });

        });
    }

    // Función para mostrar mensajes flash debajo del botón enviar
    function showFlashMessage(message, category) {
        const flashContainer = document.getElementById("flash-messages");

        // Limpiar mensajes previos
        flashContainer.innerHTML = "";

        const flashMessage = document.createElement("div");
        flashMessage.className = `alert ${category}`;
        flashMessage.textContent = message;

        flashContainer.appendChild(flashMessage);

        setTimeout(() => {
            flashMessage.remove();
        }, 5000);
    }
});
