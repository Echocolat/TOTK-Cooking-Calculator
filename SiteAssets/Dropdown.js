async function fetchJson(url) {
    try {
      // Fetch the JSON file
      const response = await fetch(url);
      
      // Check if the response is successful
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // Parse and return the JSON data
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching JSON data:', error);
      // Optionally rethrow the error if you want to handle it further up the call chain
      throw error;
    }
}

function createDropdown(options, id) {
    const selectElement = document.getElementById(id);

    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.textContent = option;
        optionElement.value = option;
        selectElement.appendChild(optionElement);
    });
}

async function makeMatDropdown(id) {
    const MaterialData = await fetchJson('./Data/MaterialData.json');
    const LanguageData = await fetchJson('./Data/LanguageData.json');
    const lang = "EUen";

    let options = [''];

    for (let i = 0; i < MaterialData.length; ++i) {
        const key = MaterialData[i];
        const actorName = key["ActorName"];
        const nameKey = `${actorName}_Name`;
        options.push(LanguageData["Material"][nameKey][lang]);
    };

    createDropdown(options, id);
};

const container = document.getElementById('items');

for (let i = 1; i <= 5; i++) {
    const select = document.createElement('select');
    select.id = `item${i}`;
    select.className = "entry"
    container.appendChild(select);
    makeMatDropdown(select.id);
}