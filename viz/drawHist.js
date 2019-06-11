function drawHist(govName, party, targetDiv, hasLegend) {

  var filepath = `output/governos/${govName}-${party}.csv`;

  // This json is used to add a dynamic legend
  var historicalData = "output/historicos.json";

  /*
  Reads the data in!
  When it's finished, it runs the function 'ready'
  */
  d3.queue()
    .defer(d3.csv, filepath)
    .defer(d3.json, historicalData)
    .await(ready);

  // Let's hide the chart so we don't have a "delay"
  // after the user clicks a button
  d3.select(".main-hist-container").style("opacity", 0);
  d3.select(".big-legend").style("opacity", 0);

  // Reveals the loading button
  d3.select(".lds-dual-ring").classed("loading", true);

  // After the data is loaded, this function runs
  function ready(error, datapoints, historicalData) {

    console.log(datapoints);

    /* If a histogram is already drawn,
    we first need to clean it */

    d3.select(".main-hist-container").remove();

    /*
    Discovers the highest vote count
    for a representative in order to
    give each point the right opacity.
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

    /* Now we will create the HTML
    structure dynamically
    */

    const histContainer = d3.select(targetDiv)
      .append("div")
      .attr("class", "main-hist-container")

    const labelContainer = histContainer
        .append("div")
        .attr("class", "label-container")

    labelContainer.append("span")
      .attr("class", "label-oposicao")
      .html("← Oposição")

    labelContainer.append("span")
      .attr("class", "label-aliado")
      .html("Aliado →")

    const scaleContainer = histContainer
      .append("div")
      .attr("class", "scale-container")

    scaleContainer.append("span")
      .html("0");
    scaleContainer.append("span")
      .html("50");
    scaleContainer.append("span")
      .html("100%");

    /*
    Onto the real chart!
    Selects the figure and adds a
    inner div for each bin in the
    histogram.
    */
    const hist = histContainer
      .append("div")
      .attr("class", "hist")
      .attr("data-governo", govName);

    const groups = hist
      .selectAll(".hist-bar")
      .data(bins)
      .enter().append("div")
      .attr("class", "group")
      .attr("data-bin", function(d){
        return d;
      })
      .each(function(d){

        /*
        In each group, adds the respective
        datapoints on top of one another
        */

        /*
        1. Filtering datapoints to keep
        only the relevant values
        */

        selectedValues = datapoints.filter(function(e){
            return (+e.proGovPct == d);
        })

        /*
        2. Sorting them in a way that will have
        all the low-opacity points at the outer
        end of the graphic.
        */

        selectedValues = selectedValues.sort(function(a,b){
          return b.totalVotos - a.totalVotos;
        })

        /*
        3. Adding the relevant datapoints
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


      });


    // if hasLegend is true, we will write HTML to a h2 element
    if (hasLegend) {

      // Selects the element
      var bigLegend = d3.select(".big-legend");

      // Selects the historical data
      var allTimeData = Math.round(historicalData["historico"] * 100 );
      var thisGovData = Math.round( historicalData[govName] * 100);

      // Composes the string in this totally weird way
      if (thisGovData > allTimeData) {
        var comparison = "diferente";
        var comparisonString = "acima da taxa histórica de";
        var color = '#00a79d';
        var backgroundColor = '#c2e8e5';
      }
      else if (thisGovData == allTimeData) {
        var comparison = "igual";
        var comparisonString = "valor igual à taxa histórica";
        var color = '#2d4aad';
        var backgroundColor = '#c8cee4';
      }
      else if (thisGovData < allTimeData) {
        var comparison = "diferente";
        var comparisonString = "abaixo da taxa histórica de";
        var color = "#c441c4";
        var backgroundColor = "#efc6ef";
      }

      switch (govName) {
        case "Bolsonaro 1":
          var legendName = "mandato de Bolsonaro";
          break
        case "Temer 1":
          var legendName = "mandato de Temer";
          break
        case "Dilma 2":
          var legendName = "2º mandato de Dilma";
          break
        case "Dilma 1":
          var legendName = "1º mandato de Dilma";
          break
        case "Lula 2":
          var legendName = "2º mandato de Lula";
          break
        case "Lula 1":
          var legendName = "1º mandato de Lula";
          break
      }

      switch (comparison) {
        case "diferente":
          var legendContent = `
          Durante o ${legendName}, o Congresso votou de acordo com as orientações do governo
          <span class="support-count">${thisGovData}% das vezes</span>, ${comparisonString} ${allTimeData}%
          `;
          break

        case "igual":
          var legendContent = `
          Durante o ${legendName}, o Congresso votou de acordo com as orientações do governo
          <span class="support-count">${thisGovData}% das vezes</span>, ${comparisonString}
          `;
          break
      }

    // Updates the html
    bigLegend.html(legendContent);

    // Selects and updates the span color
    d3.select(".support-count")
      .style("color", color)
      .style("background-color", backgroundColor);

    }


    // Initializates the legend using the Tippy package
    // https://atomiks.github.io/tippyjs/
    tippy(".block", {
      arrow: true,
      theme: 'basometro',
      maxWidth: '250px',
    });

  // Displays everything again
  d3.select(".main-hist-container").style("opacity", 1);
  d3.select(".big-legend").style("opacity", 1);

  // Hides the loading button
  d3.select(".lds-dual-ring").classed("loading", false);



  }

}
