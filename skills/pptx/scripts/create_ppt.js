#!/usr/bin/env node
/**
 * Simple PowerPoint Generator for AgentCore Runtime
 * 
 * Usage:
 *   node create_simple_pptx.js <output_path> <title> <slide1_content> [slide2_content] ...
 * 
 * Example:
 *   node create_simple_pptx.js /app/output.pptx "Tokyo Tower" "History: Built in 1958" "Structure: 333m tall"
 */

const pptxgen = require('pptxgenjs');
const path = require('path');
const fs = require('fs');

async function createSimplePresentation(outputPath, title, slideContents) {
  try {
    console.log('Initializing PowerPoint...');
    const pptx = new pptxgen();
    pptx.layout = 'LAYOUT_16x9';
    pptx.author = 'Strands Agent';
    pptx.title = title;

    // Title Slide
    console.log('Creating title slide...');
    const titleSlide = pptx.addSlide();
    titleSlide.background = { color: '1F4788' };
    titleSlide.addText(title, {
      x: 0.5,
      y: 1.5,
      w: 9,
      h: 1.5,
      fontSize: 44,
      bold: true,
      color: 'FFFFFF',
      align: 'center',
      valign: 'middle'
    });
    titleSlide.addText('Powered by Strands AI Agent', {
      x: 0.5,
      y: 3.5,
      w: 9,
      h: 0.5,
      fontSize: 18,
      color: 'E8E8E8',
      align: 'center'
    });

    // Content Slides
    slideContents.forEach((content, index) => {
      console.log(`Creating slide ${index + 2}: ${content.substring(0, 30)}...`);
      const slide = pptx.addSlide();
      slide.background = { color: 'FFFFFF' };

      // Slide title
      const lines = content.split('\n');
      const slideTitle = lines[0] || `Slide ${index + 1}`;
      const slideBody = lines.slice(1).join('\n') || content;

      slide.addText(slideTitle, {
        x: 0.5,
        y: 0.5,
        w: 9,
        h: 0.8,
        fontSize: 32,
        bold: true,
        color: '1F4788'
      });

      // Slide content
      slide.addText(slideBody, {
        x: 0.5,
        y: 1.5,
        w: 9,
        h: 4,
        fontSize: 18,
        color: '333333',
        valign: 'top',
        bullet: slideBody.includes('\n') ? { type: 'bullet' } : false
      });
    });

    // Save the presentation
    console.log(`Saving to ${outputPath}...`);

    // Ensure output directory exists
    const outputDir = path.dirname(outputPath);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    await pptx.writeFile({ fileName: outputPath });

    console.log(`✓ Successfully created PowerPoint: ${outputPath}`);
    console.log(`  - Title: ${title}`);
    console.log(`  - Total slides: ${slideContents.length + 1}`);

    // Verify file exists and get size
    const stats = fs.statSync(outputPath);
    console.log(`  - File size: ${(stats.size / 1024).toFixed(2)} KB`);

    return { success: true, path: outputPath, size: stats.size };

  } catch (error) {
    console.error(`✗ Error creating PowerPoint: ${error.message}`);
    console.error(error.stack);
    return { success: false, error: error.message };
  }
}

// Main execution
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.error('Usage: node create_simple_pptx.js [output_path] <title> <slide1_content> [slide2_content] ...');
    console.error('Example: node create_simple_pptx.js "My Presentation" "Slide 1 content" "Slide 2 content"');
    console.error('Or: node create_simple_pptx.js output.pptx "My Presentation" "Slide 1 content" "Slide 2 content"');
    process.exit(1);
  }

  // Smart argument parsing: check if first arg is a file path (ends with .pptx) or a title
  let outputPath, title, slideContents;

  if (args[0].endsWith('.pptx')) {
    // Traditional format: <output_path> <title> <slides...>
    outputPath = args[0];
    title = args[1];
    slideContents = args.slice(2);
  } else {
    // Agent format: <title> <slides...> (use default output path)
    outputPath = '/app/output.pptx';
    title = args[0];
    slideContents = args.slice(1);
  }

  if (slideContents.length === 0) {
    console.error('Error: At least one slide content is required');
    process.exit(1);
  }

  createSimplePresentation(outputPath, title, slideContents)
    .then(result => {
      if (result.success) {
        process.exit(0);
      } else {
        process.exit(1);
      }
    })
    .catch(error => {
      console.error('Unexpected error:', error);
      process.exit(1);
    });
}

module.exports = { createSimplePresentation };
