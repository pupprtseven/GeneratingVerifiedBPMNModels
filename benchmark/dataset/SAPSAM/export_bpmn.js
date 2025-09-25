const fs = require('fs');
const path = require('path');
const csv = require('csv-parser');
const BpmnModdle = require('bpmn-moddle').default;
const { create } = require('bpmn-js/lib/Modeler');

// Create output directories
const outputDir = 'BPMN2.0_LOCAL';
const collaborationDir = path.join(outputDir, 'collaboration');
const standardDir = path.join(outputDir, 'standard');

if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
}
if (!fs.existsSync(collaborationDir)) {
    fs.mkdirSync(collaborationDir, { recursive: true });
}
if (!fs.existsSync(standardDir)) {
    fs.mkdirSync(standardDir, { recursive: true });
}

// Check if contains Subprocess
function containsSubprocess(modelJson) {
    return modelJson.includes('"stencil":{"id":"Subprocess"');
}

// Check if it's a collaboration diagram
function isCollaboration(modelJson, namespace) {
    const hasParticipant = modelJson.toLowerCase().includes('participant');
    const hasCollaboration = modelJson.toLowerCase().includes('collaboration');
    const isChoreography = namespace === 'http://b3mn.org/stencilset/bpmn2.0choreography#';

    return hasParticipant || hasCollaboration || isChoreography;
}

// Sanitize filename
function sanitizeFilename(filename) {
    return filename.replace(/[<>:"/\\|?*]/g, '_').substring(0, 100);
}

// Process single model
async function processModel(modelJson, modelName, namespace, index) {
    try {
        // Check if contains Subprocess
        if (containsSubprocess(modelJson)) {
            console.log(`Skipping model with Subprocess: ${modelName}`);
            return;
        }

        // Determine if it's a collaboration diagram
        const isCollab = isCollaboration(modelJson, namespace);

        // Generate filename
        const safeName = sanitizeFilename(modelName);
        const filename = `${index}_${safeName}.bpmn`;
        const targetDir = isCollab ? collaborationDir : standardDir;
        const filePath = path.join(targetDir, filename);

        // Create model using bpmn-js
        const modeler = create({
            container: '#canvas',
            keyboard: {
                bindTo: window
            }
        });

        // Import JSON data
        const { warnings } = await modeler.importJSON(JSON.parse(modelJson));

        if (warnings.length) {
            console.log(`Model ${modelName} has warnings:`, warnings);
        }

        // Export to XML
        const { xml } = await modeler.saveXML({ format: true });

        // Save file
        fs.writeFileSync(filePath, xml, 'utf8');

        console.log(`Saved: ${filePath}`);

        return { success: true, isCollaboration: isCollab };

    } catch (error) {
        console.error(`Error processing model ${modelName}:`, error.message);
        return { success: false, error: error.message };
    }
}

// Main processing function
async function processCSVFiles() {
    console.log('Starting to process CSV files...');

    const csvDir = path.join('data', 'raw', 'models');
    const csvFiles = fs.readdirSync(csvDir).filter(file => file.endsWith('.csv'));

    console.log(`Found ${csvFiles.length} CSV files`);

    let totalProcessed = 0;
    let collaborationCount = 0;
    let standardCount = 0;
    let index = 1;

    for (const csvFile of csvFiles) {
        const csvPath = path.join(csvDir, csvFile);
        console.log(`Processing file: ${csvFile}`);

        const results = [];

        // Read CSV file
        fs.createReadStream(csvPath)
            .pipe(csv())
            .on('data', (row) => {
                // Only process BPMN2.0 flowcharts
                if (row.namespace === 'http://b3mn.org/stencilset/bpmn2.0#') {
                    results.push({
                        modelJson: row.model_json,
                        modelName: row.name,
                        namespace: row.namespace
                    });
                }
            })
            .on('end', async () => {
                console.log(`Found ${results.length} BPMN2.0 models in file ${csvFile}`);

                // Process each model
                for (const result of results) {
                    const processResult = await processModel(
                        result.modelJson,
                        result.modelName,
                        result.namespace,
                        index++
                    );

                    if (processResult && processResult.success) {
                        totalProcessed++;
                        if (processResult.isCollaboration) {
                            collaborationCount++;
                        } else {
                            standardCount++;
                        }

                        // Output progress every 100 files
                        if (totalProcessed % 100 === 0) {
                            console.log(`Processed ${totalProcessed} models...`);
                        }
                    }
                }
            });
    }

    console.log('\nExport completed!');
    console.log(`Total processed: ${totalProcessed} models`);
    console.log(`Collaboration diagrams: ${collaborationCount}`);
    console.log(`Standard flowcharts: ${standardCount}`);
    console.log(`Files saved in: ${path.resolve(outputDir)}`);
    console.log(`  - Collaboration diagrams: ${path.resolve(collaborationDir)}`);
    console.log(`  - Standard flowcharts: ${path.resolve(standardDir)}`);
}

// Run main function
processCSVFiles().catch(console.error); 