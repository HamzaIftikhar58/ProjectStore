/**
 * UI Modals
 */

'use strict';

(function () {
  // Animation Dropdown
  const animationDropdown = document.querySelector('#animation-dropdown'),
    animationModal = document.querySelector('#animationModal');
  if (animationDropdown) {
    animationDropdown.onchange = function () {
      animationModal.classList = '';
      animationModal.classList.add('modal', 'animate__animated', this.value);
    };
  }

  // On hiding modal, remove iframe video/audio to stop playing
  const youTubeModal = document.querySelector('#youTubeModal'),
    youTubeModalVideo = youTubeModal.querySelector('iframe');
  youTubeModal.addEventListener('hidden.bs.modal', function () {
    youTubeModalVideo.setAttribute('src', '');
  });

  // Function to get and auto play youTube video
  const autoPlayYouTubeModal = function () {
    const modalTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="modal"]'));
    modalTriggerList.map(function (modalTriggerEl) {
      modalTriggerEl.onclick = function () {
        const theModal = this.getAttribute('data-bs-target'),
          videoSRC = this.getAttribute('data-theVideo'),
          videoSRCauto = `${videoSRC}?autoplay=1`,
          modalVideo = document.querySelector(`${theModal} iframe`);
        if (modalVideo) {
          modalVideo.setAttribute('src', videoSRCauto);
        }
      };
    });
  };

  // Calling function on load
  autoPlayYouTubeModal();

  // Onboarding modal carousel height animation
  document.querySelectorAll('.carousel').forEach(carousel => {
    carousel.addEventListener('slide.bs.carousel', event => {
      // Get next slide height
      const nextH = getHiddenHeight(event.relatedTarget);
      // Find the carousel items container (usually .carousel-inner)
      const activeItem = carousel.querySelector('.active.carousel-item');
      const container = activeItem ? activeItem.parentElement : carousel.querySelector('.carousel-inner');

      if (container) {
        const currentH = container.offsetHeight;
        if (currentH !== nextH) {
          container.style.transition = 'height 0.5s ease';
          container.style.height = `${currentH}px`;
          // Force reflow to ensure the start height is applied before transition
          container.offsetHeight;
          container.style.height = `${nextH}px`;
        }
      }
    });
  });

  // Helper function to get height of hidden element
  function getHiddenHeight(el) {
    if (!el) return 0;
    const style = window.getComputedStyle(el);
    if (style.display !== 'none') return el.offsetHeight;

    const prevVisibility = el.style.visibility;
    const prevPosition = el.style.position;
    const prevDisplay = el.style.display;

    el.style.visibility = 'hidden';
    el.style.position = 'absolute';
    el.style.display = 'block';

    const height = el.offsetHeight;

    el.style.display = prevDisplay;
    el.style.position = prevPosition;
    el.style.visibility = prevVisibility;

    return height;
  }
})();
