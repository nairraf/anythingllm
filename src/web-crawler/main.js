import { PlaywrightCrawler } from 'crawlee';
import { appendFileSync, existsSync } from 'fs';
import { readFile } from 'fs/promises';

const links = './links.json'


const runCrawler = async (startUrl, outputFile, globs) => {
    // Check if the output file already exists
    if (existsSync(outputFile)) {
        console.log(`Skipping crawl for: ${startUrl}. '${outputFile}' exists.\n`);
        return; // Exit the function early
    }

    const foundUrls = new Set();
    
    const crawler = new PlaywrightCrawler({
        maxConcurrency: 20,
        async requestHandler({ request, enqueueLinks, log }) {
            foundUrls.add(request.url);

            //log.info(`Processing ${request.url}...`);
            //const currentUrl = request.url;
            //appendFileSync(outputFile, currentUrl + '\n');
            //log.info(`Added URL to ${outputFile}`);

            await enqueueLinks({
                globs: globs,
            });
        },
        // The maxRequestsPerCrawl value is removed to allow for full crawls.
        // You can re-add it as a parameter if needed.
    });

    try {
        await crawler.run([startUrl]);
    } finally {
        await crawler.teardown();
    }

    // <<< Corrected: Write the local Set to the file once
    console.log(`Crawl finished. found ${foundUrls.size} links`);

    appendFileSync(outputFile, [...foundUrls].join('\n'));

    console.log(`Crawl finished. All URLs are in the ${outputFile} file.`);
};


   // {
    //     "url": "https://github.com/microsoft/dotnet",
    //     "outfile": "dotnet_github_urls.txt",
    //     "globs": ["https://github.com/microsoft/dotnet/blob/**/*.md"]
    // }

const main = async () => {
    let crawlJobs;
    try {
        const fileContent = await readFile(links, 'utf8');
        crawlJobs = JSON.parse(fileContent);
    } catch (error) {
        console.error(`Error reading or parsing config file: ${error.message}`);
        process.exit(1); // Exit with an error code
    }

    for (const job of crawlJobs) {
        console.log(`Starting crawl for: ${job.url}`);
        await runCrawler(job.url, job.outfile, job.globs);
    }
};

main();