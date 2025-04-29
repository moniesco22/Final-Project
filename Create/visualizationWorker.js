self.onmessage = function(event) {
  const { id, data } = event.data;
  let progress = 0;

  // Simulate progress updates
  const interval = setInterval(() => {
    progress += 20;
    self.postMessage({ progress });

    if (progress === 100) {
      clearInterval(interval);

      // Generate SVG content dynamically (example for bar chart)
      const margin = { top: 20, right: 20, bottom: 50, left: 50 };
      const width = 600 - margin.left - margin.right;
      const height = 400 - margin.top - margin.bottom;

      const svgContent = `
        <svg width="${width + margin.left + margin.right}" height="${height + margin.top + margin.bottom}">
          <g transform="translate(${margin.left},${margin.top})">
            ${data.map((d, i) => {
              const x = i * (width / data.length);
              const y = height - (d.value / Math.max(...data.map(d => d.value))) * height;
              const barHeight = (d.value / Math.max(...data.map(d => d.value))) * height;
              return `
                <rect x="${x}" y="${y}" width="${width / data.length - 2}" height="${barHeight}" fill="steelblue" data-id="${id}-${i}"></rect>
              `;
            }).join('')}
          </g>
        </svg>
      `;

      self.postMessage({ progress: 100, svgContent });
    }
  }, 500);
};