function drawSmallHists(govName, targetDiv) {

  /* 
  Draws the small multiples in the home page of the app
  
  Params:

  govName: which government to draw, defined by user interaction in the app
  targetDiv: a CSS selector that determines where to draw the small multiples */

  // Which parties should we draw for each govName? \
  // It's always the 5/10 biggest in the beggining of each legislature
  switch (govName) {
    case "Bolsonaro 1":
      var parties = [ "PT", "PSL", "Progressistas", "PSD", "MDB", ] // "PR", "PSB", "PRB", "DEM", "PSDB" ];
      break;
    case "Temer 1":
      var parties = [ "PT", "MDB", "Progressistas", "PSDB", "DEM", ] // "PR",  "PSD", "PRB", "PDT", "PODE" ];
      break;
    case "Dilma 2":
      var parties = [ "PT", "MDB", "Progressistas", "PSDB", "DEM", ] // "PR", ]  "PSD", "PRB", "PDT", "PODE" ];
    case "Dilma 1":
      var parties = [ "PT", "MDB", "PSDB", "DEM", "Progressistas", ] //"PR", "PSB", "PDT", "PTB", "PSC" ];
      break;
    case "Lula 2":
      var parties = [ "PT", "MDB", "PSDB", "DEM", "Progressistas", ] //"PSB",  "PDT", "PTB", "PR", "Cidadania" ];
      break;
    case "Lula 1":
      var parties = [ "PT", "DEM", "MDB", "PSDB", "Progressistas", ] // "PR",  "PTB", "PSB", "PDT", "Cidadania" ];
      break;
  }

  // Let's gather their filepaths
  var filepaths = [ ]
  for (i = 0; i < parties.length; i++) {
    var filepath = `output/governos/${govName}-${parties[i]}.csv`;
    filepaths.push(filepath);
  }

  console.assert(filepaths.length === 5, "We have the wrong number of parties, pal");
  
  // This json is used to add a dynamic legend comparing the vote rate in each gov
  // By default, this isn't used in the small multiples, but we left in here in case
  // we made different design decision later on
  var historicalData = "output/historicos.json";

  // Hides the container
  d3.select(".outer-container").style("opacity", 0);

  // Reveals the loading button
  d3.select(".lds-dual-ring-secondary").classed("loading", true);

  /*
  Reads the data in!
  When it's finished, it runs the function 'ready'
  */
  d3.queue()
    .defer(d3.csv, filepaths[0])
    .defer(d3.csv, filepaths[1])
    .defer(d3.csv, filepaths[2])
    .defer(d3.csv, filepaths[3])
    .defer(d3.csv, filepaths[4])
    .defer(d3.json, historicalData)
    .await(ready);


  // After the data is loaded, this function runs
  function ready(error, datapoints0, datapoints1, datapoints2, 
                datapoints3, datapoints4, historicalData) {

    /* If a histogram is already drawn,
    we first need to clean it */
    d3.select(".outer-container").remove();

    // To make our life easier, let's merge all the data objects into a single one.
    var datapoints = datapoints0.concat(datapoints1, datapoints2, datapoints3, datapoints4);

    /*
    Discovers the highest vote count
    for a representative in order to
    give each point the right opacity.
    We explicitly decided to do so, 
    instead of using a percentage, to
    account for different political
    contexts –  so we thought the viz
    should compare the assiduity among
    a single legislature and not across
    all of them.
    */
    const maxVotes = d3.max(
      datapoints.map(function(d) {
          return +d.totalVotos;
        })
      )

    /* Custom color and opacity scales */
    const opacityScale = d3.scaleLinear()
      .domain([0, maxVotes])
      .range([0, 1])

    const colorScale = d3.scaleLinear()
      .domain([0, 1])
      .range(["#c441c4", "#00a79d"])

    /*
    Creates an array with
    all the histogram bins
    */

    var bins = [ ];
    for (i = 0; i <= 100; i++) {

      val  = (i / 100).toFixed(2);
      bins.push( val );
    }

    /* Now we need to nest the datapoints by party so we can add a 
    chart for each one of them */

    const nested = d3.nest()
      .key(function(d){
        return d.partido;
      })
      .entries(datapoints);

    /* 
    Now we will create the HTML structure dynamically
    while drawing the charts
    */


    // Adds a wrapper for all the charts
    const outerContainer = d3.select(targetDiv)
      .append("div")
      .attr("class", "outer-container");

    // Appends a chart for each party
    const innerContainers = outerContainer.selectAll(".small-multiples")
      .data(nested)
      .enter().append("div")
      .attr("class", "small-multiple");

    // In each div, add the relevant title
    innerContainers.append("h2")
      .attr("class", "chart-title")
      .html(function(d){
        return d.key;
      })

    // Adding labels
    const labelContainers = innerContainers.append("div")
      .attr("class", "label-container");

    labelContainers.append("span")
      .attr("class", "label-oposicao")
      .html("← Oposição");

    labelContainers.append("span")
      .attr("class", "label-aliado")
      .html("Aliado →");

    // Then the scales
    const scaleContainers = innerContainers.append("div")
      .attr("class", "scale-container");

    scaleContainers.append("span")
      .html("0");
    scaleContainers.append("span")
      .html("50");
    scaleContainers.append("span")
      .html("100%");

    // And now the real charts! Hooray!!!!
    const histContainers = innerContainers.append('div')
      .attr("class", "hist-container");

    const hists = histContainers.append("div")
      .attr("class", "hist")
      .attr("data-partido", function(d){
        return d.key;
      })

    const groups = hists.selectAll(".hist-bar")
      .data(bins)
      .enter().append("div")
      .attr("class", "group")
      .each(function(d) {
        /*
        In each group, adds the respective
        datapoints on top of one another
        */

        /*
        1. Filtering datapoints to keep
        only the party values
        */

        var thisParty = d3.select(this.parentNode).attr("data-partido");
        var selectedValues = nested.filter(function(x){
          return x.key == thisParty;
        })[0].values;

        /*
        2. Filtering datapoints to keep
        only the values within the desired bin
        */
        selectedValues = selectedValues.filter(function(e){
            return (+e.proGovPct == d);
        })

        /*
        3. Sorting them in a way that will have
        all the low-opacity points at the outer
        end of the graphic.
        */

        selectedValues = selectedValues.sort(function(a,b){
          return b.totalVotos - a.totalVotos;
        })

        /*
        4. Adding the relevant datapoints
        */
        innerGroup = d3.select(this);

        innerGroup.selectAll(".block")
          .data(selectedValues)
          .enter().append("div")
          .attr("class", "block")
          .attr("width", "100%")
          .attr("data-parlamentar", function(d) {
            return d.parlamentar;
          })
          .attr("data-proGovPct", function(d) {
            return d.proGovPct;
          })
          .attr('data-proGovCtg', function(d){
            return d.proGovCtg;
          })
          .style("opacity", function(d){
            return opacityScale(+d.totalVotos);
          })
          .style("background-color", function(d){
            return colorScale(+d.proGovPct);
          })
          .attr("data-tippy-content", function(d){

            if (+d.proGovPct >= .5) {

              var htmlContent = `
              <span class="tooltip-name">${d.parlamentar}</span>
              <span class="tooltip-info">${d.partido} | ${d.uf}</span></br>
              <span class="tooltip-long-desc">Votou ${d.proGovCtg} vezes <strong class="pro">a favor</strong> do governo</br>
              É <strong>${Math.round(d.proGovPct * 100)}%</strong> governista </br>
              Participou de <strong>${Math.round(d.assiduidadeParlamentar * 100)}%</strong> das sessões</span>
              `

            }

            else {
              var htmlContent = `
              <span class="tooltip-name">${d.parlamentar}</span>
              <span class="tooltip-info">${d.partido} | ${d.uf}</span></br>
              <span class="tooltip-long-desc">Votou ${d.antiGovCtg} vezes <strong class="against">contra</strong> o governo</br>
              É <strong>${Math.round(d.proGovPct * 100)}%</strong> governista</br>
              Participou de <strong>${Math.round(d.assiduidadeParlamentar * 100)}%</strong> das sessões</span>
              `
            }
            return htmlContent;
          })
          .on("mouseover", function(d){
            var element = d3.select(this);
            element.style("background-color", "#636363");
          })
          .on("mouseout", function(d){
            var element = d3.select(this);
            element.style("background-color", colorScale(+d.proGovPct));
          });

      })

  tippy(".block", {
    arrow: true,
    theme: 'basometro',
    maxWidth: '250px',
  });

  // Shows the container
  d3.select(".outer-container").style("opacity", 1);

  // Hides the loading button
  d3.select(".lds-dual-ring-secondary").classed("loading", false);

  }

}
