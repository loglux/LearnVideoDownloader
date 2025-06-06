import re

def find_changing_block(url1, url2):
    """
    Finds the index of the numeric block that changes between url1 and url2.
    Returns (block_index, value1, value2, width)
    """
    numbers1 = list(re.finditer(r'\d+', url1))
    numbers2 = list(re.finditer(r'\d+', url2))
    for i, (m1, m2) in enumerate(zip(numbers1, numbers2)):
        if m1.group() != m2.group():
            return i, m1.group(), m2.group(), len(m1.group())
    return None

def generate_urls_from_pattern(sample_url1, sample_url2, count):
    """
    Generates a list of URLs by automatically detecting the numeric block to increment,
    based on two sample URLs. Always generates sequence starting from 1 regardless of 
    the sample URL numbers.
    
    Args:
        sample_url1: First sample URL (e.g. ".../module-4")
        sample_url2: Second sample URL (e.g. ".../module-5")
        count: Number of URLs to generate, starting from 1
    
    Returns:
        List of generated URLs with numbers from 1 to count
    """
    result = []
    block_info = find_changing_block(sample_url1, sample_url2)
    if not block_info:
        print("No changing numeric block found between the two samples.")
        return []
    
    block_index, value1, value2, width = block_info
    # Find the start and end position of the block to replace
    matches = list(re.finditer(r'\d+', sample_url1))
    start, end = matches[block_index].span()
    
    # Always start from 1, regardless of the sample URL numbers
    for i in range(count):
        number = str(i + 1).zfill(width)  # i + 1 to start from 1 instead of 0
        new_url = sample_url1[:start] + number + sample_url1[end:]
        result.append(new_url)
    return result

if __name__ == "__main__":
    # Example with non-sequential sample URLs
    sample_url1 = "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-4"
    sample_url2 = "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-5"
    count = 5

    urls = generate_urls_from_pattern(sample_url1, sample_url2, count)
    print("Generated URLs:")
    for url in urls:
        print(url)  # Will print URLs with numbers 1,2,3,4,5 regardless of sample URLs being 4,5 