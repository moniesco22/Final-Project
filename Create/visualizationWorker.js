function generateEngagementVisualization(data) {
  const margin = { top: 20, right: 20, bottom: 50, left: 50 };
  const width = 600 - margin.left - margin.right;
  const height = 400 - margin.top - margin.bottom;

  const svgContent = `
    <svg width="${width + margin.left + margin.right}" height="${height + margin.top + margin.bottom}">
      <g transform="translate(${margin.left},${margin.top})">
        ${data.map((d, i) => {
          const x = i * (width / data.length);
          const y = height - (d.total_spend / Math.max(...data.map(d => d.total_spend))) * height;
          const barHeight = (d.total_spend / Math.max(...data.map(d => d.total_spend))) * height;
          return `
            <rect x="${x}" y="${y}" width="${width / data.length - 2}" height="${barHeight}" fill="steelblue" data-id="engagement-${i}"></rect>
          `;
        }).join('')}
      </g>
    </svg>
  `;

  return svgContent;
}

function generateDemographicsVisualization(data) {
  // Placeholder for demographics visualization logic
  return '<svg><text x="10" y="20">Demographics Visualization</text></svg>';
}

// Add more visualization functions here...

self.onmessage = function(event) {
  const { id, data } = event.data;
  let progress = 0;

  const interval = setInterval(() => {
    progress += 20;
    self.postMessage({ progress });

    if (progress === 100) {
      clearInterval(interval);

      let svgContent = '';
      switch (id) {
        case 'engagement':
          svgContent = generateEngagementVisualization(data);
          break;
        case 'demographics':
          svgContent = generateDemographicsVisualization(data);
          break;
        // Add more cases for other visualizations...
        default:
          svgContent = '<svg><text x="10" y="20">Unknown Visualization</text></svg>';
      }

      self.postMessage({ progress: 100, svgContent });
    }
  }, 500);
};