/**
 * Сезонные эффекты:
 * - Зима (декабрь, январь, февраль) - снег
 * - Весна (март, апрель, май) - лепестки сакуры
 * - Лето (июнь, июль, август) - ничего
 * - Осень (сентябрь, октябрь, ноябрь) - листопад
 */

document.addEventListener('DOMContentLoaded', function() {
  const currentMonth = new Date().getMonth() + 1; // 1-12

  let season = '';
  let effectConfig = {};

  // Определяем сезон
  if (currentMonth >= 12 || currentMonth <= 2) {
    // Зима: декабрь, январь, февраль
    season = 'winter';
    effectConfig = {
      type: 'snow',
      enabled: true
    };
  } else if (currentMonth >= 3 && currentMonth <= 5) {
    // Весна: март, апрель, май
    season = 'spring'; //spring
    effectConfig = {
      type: 'sakura', //sakura
      enabled: true
    };
  } else if (currentMonth >= 6 && currentMonth <= 8) {
    // Лето: июнь, июль, август
    season = 'summer';
    effectConfig = {
      type: 'none',
      enabled: false
    };
  } else {
    // Осень: сентябрь, октябрь, ноябрь
    season = 'autumn';
    effectConfig = {
      type: 'leaves',
      enabled: true
    };
  }

  // Применяем эффекты
  if (effectConfig.enabled) {
    applySeasonalEffect(effectConfig.type);
  }
});

function applySeasonalEffect(type) {
  switch(type) {
    case 'snow':
      initSnowEffect();
      break;
    case 'sakura':
      initSakuraEffect();
      break;
    case 'leaves':
      initLeavesEffect();
      break;
    case 'none':
    default:
      // Никаких эффектов
      break;
  }
}

// Эффект снега (использует библиотеку Snow.js)
function initSnowEffect() {
  // Сначала загружаем CSS
  if (!document.getElementById('snow-css')) {
    const cssLink = document.createElement('link');
    cssLink.id = 'snow-css';
    cssLink.rel = 'stylesheet';
    cssLink.href = 'https://cdn.jsdelivr.net/gh/Alaev-Co/snowflakes/dist/snow.min.css';
    document.head.appendChild(cssLink);
  }

  // Функция инициализации снега
  function createSnow() {
    if (typeof Snow !== 'undefined') {
      new Snow({
        iconColor: '#ffffff',
        iconSize: 15,
        showSnowBalls: false,  // ОТКЛЮЧАЕМ сугробы - они создают линию внизу
        showSnowBallsIsMobile: false,
        showSnowflakes: true,
        countSnowflake: 80,
        snowBallsLength: 0
      });
    }
  }

  // Проверяем, загружена ли библиотека
  if (typeof Snow !== 'undefined') {
    createSnow();
  } else {
    // Динамически загружаем библиотеку
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/gh/Alaev-Co/snowflakes/dist/Snow.min.js';
    script.onload = function() {
      createSnow();
    };
    document.body.appendChild(script);
  }
}

// Эффект лепестков сакуры
function initSakuraEffect() {
  // Создаем контейнер для лепестков
  const container = document.createElement('div');
  container.id = 'sakura-container';
  container.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 9999;
    overflow: hidden;
  `;
  document.body.appendChild(container);
  
  // Создаем лепестки
  const petalCount = 30;
  for (let i = 0; i < petalCount; i++) {
    createSakuraPetal(container);
  }
}

function createSakuraPetal(container) {
  const petal = document.createElement('div');
  petal.style.cssText = `
    position: absolute;
    top: -20px;
    left: ${Math.random() * 100}%;
    width: ${8 + Math.random() * 8}px;
    height: ${10 + Math.random() * 8}px;
    background: linear-gradient(135deg, #ffb7c5 0%, #ffc0cb 50%, #ffe4e1 100%);
    border-radius: 50% 0 50% 50%;
    opacity: ${0.6 + Math.random() * 0.3};
    animation: sakuraFall ${8 + Math.random() * 6}s linear infinite;
    animation-delay: ${Math.random() * 10}s;
    transform: rotate(${Math.random() * 360}deg);
  `;
  container.appendChild(petal);
  
  // Добавляем CSS анимацию если её нет
  if (!document.getElementById('sakura-style')) {
    const style = document.createElement('style');
    style.id = 'sakura-style';
    style.textContent = `
      @keyframes sakuraFall {
        0% {
          transform: translateY(-20px) rotate(0deg) translateX(0px);
          opacity: 0;
        }
        10% {
          opacity: 0.8;
        }
        90% {
          opacity: 0.6;
        }
        100% {
          transform: translateY(100vh) rotate(720deg) translateX(${50 + Math.random() * 100}px);
          opacity: 0;
        }
      }
    `;
    document.head.appendChild(style);
  }
}

// Эффект листопада
function initLeavesEffect() {
  // Создаем контейнер для листьев
  const container = document.createElement('div');
  container.id = 'leaves-container';
  container.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 9999;
    overflow: hidden;
  `;
  document.body.appendChild(container);
  
  // Создаем листья
  const leafCount = 25;
  const leafColors = ['#d2691e', '#daa520', '#cd853f', '#b8860b', '#8b4513', '#a0522d'];
  
  for (let i = 0; i < leafCount; i++) {
    createLeaf(container, leafColors);
  }
}

function createLeaf(container, colors) {
  const leaf = document.createElement('div');
  const color = colors[Math.floor(Math.random() * colors.length)];
  
  leaf.style.cssText = `
    position: absolute;
    top: -30px;
    left: ${Math.random() * 100}%;
    width: ${12 + Math.random() * 10}px;
    height: ${15 + Math.random() * 12}px;
    background: ${color};
    border-radius: 0 50% 0 50%;
    opacity: ${0.7 + Math.random() * 0.2};
    animation: leafFall ${10 + Math.random() * 8}s linear infinite;
    animation-delay: ${Math.random() * 12}s;
    transform: rotate(${Math.random() * 360}deg);
  `;
  container.appendChild(leaf);
  
  // Добавляем CSS анимацию если её нет
  if (!document.getElementById('leaves-style')) {
    const style = document.createElement('style');
    style.id = 'leaves-style';
    style.textContent = `
      @keyframes leafFall {
        0% {
          transform: translateY(-30px) rotate(0deg) translateX(0px) scale(1);
          opacity: 0;
        }
        10% {
          opacity: 0.8;
        }
        50% {
          transform: translateY(50vh) rotate(360deg) translateX(${-50 + Math.random() * 100}px) scale(0.9);
        }
        90% {
          opacity: 0.6;
        }
        100% {
          transform: translateY(100vh) rotate(720deg) translateX(${50 + Math.random() * 100}px) scale(0.7);
          opacity: 0;
        }
      }
    `;
    document.head.appendChild(style);
  }
}
