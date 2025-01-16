/**
 * Масштабирует контейнер так, чтобы он занимал определенный процент от ширины экрана,
 * но не превышал половину высоты экрана.
 * 
 * @param containerSelector - Селектор контейнера, который нужно масштабировать.
 * @param targetWidthRatio - Доля ширины экрана, которую должен занимать контейнер
 * @param targetHeightRatio - Доля высоты экрана, которую должен занимать контейнер
 */
export function scaleContainer(
    containerSelector: string, 
    targetWidthRatio: number,
    targetHeightRatio: number
  ): void {
    const container = document.querySelector<HTMLElement>(containerSelector);
    
    if (!container) {
      console.error(`Элемент с селектором "${containerSelector}" не найден.`);
      return;
    }
  
    const resizeHandler = () => {
      const screenWidth = window.innerWidth;
      const screenHeight = window.innerHeight;
  
      const targetWidth = screenWidth * targetWidthRatio;
      const targetHeight = screenHeight * targetHeightRatio; // Половина высоты экрана
  
      const widthScale = targetWidth / container.offsetWidth;
      const heightScale = targetHeight / container.offsetHeight;
  
      // Выбираем минимальный масштаб, чтобы соблюсти оба ограничения
      const scale = Math.min(widthScale, heightScale);
  
      container.style.transform = `scale(${scale})`;
      container.style.transformOrigin = 'center center'; // Устанавливаем точку масштабирования
    };
  
    // Привязываем обработчик к событию изменения размера окна
    window.addEventListener('resize', resizeHandler);
  
    // Выполняем масштабирование при первой загрузке
    resizeHandler();
  }
  