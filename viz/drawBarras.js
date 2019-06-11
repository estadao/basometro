function drawBarras(entity, scaleType, targetDiv) {


  /*
   First we need to fine which kind of scale we will be using
   We decided to have 3 of them: one for all parties, other
   for a single party and other for a single representativa.
  */

  // According to the scaleType, we select files from a different path
  let filepath = '';

  if (scaleType == "deputados" || scaleType == "partidos")
    filepath = `output/${scaleType}/${entity}-MS.csv`;

  else if (scaleType == "todos")
    filepath = `output/partidos/${entity}-MS.csv`;


  // Are we on mobile?
  var windowWidth = window.innerWidth;
  if (windowWidth < 600) {
    var mobileScreen = true;
  }
  else {
    var mobileScreen = false;
  }

  // Are we on Safari?
  var userNavigator = navigator.userAgent;
  var isSafari = userNavigator.includes("Safari") && !userNavigator.includes("Chrome");
  console.log("isSafari?", isSafari);

  // Capitalization helper
  String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
  }

  // Let's hide the chart so we don't have a "delay"
  // after the user clicks a button
  d3.select(".bar-container").style("opacity", 0);
  d3.select('.viz-titles').style("opacity", 0);

  // Reveals the loading button
  d3.select(".lds-dual-ring").classed("loading", true);


  /*
  Reads the data in!
  When it's finished, it runs the function 'ready'
  */
  d3.queue()
    .defer(d3.csv, filepath)
    .defer(d3.json, "output/escalas.json") // A file, generated through Python, with the max value for all scales
    .defer(d3.json, "output/entity-corresp.json") // A file that contains the long description of each party name
    .await(ready);

  // After the data is loaded, this function runs
  function ready(error, datapoints, scales, corresp) {

    // Cleans the chart that is already drawn, if necessary
    d3.select(".outer-container").remove();

  // Format data in strict ISO format. This is necessary because Safari breaks
  // when using formatted like "2019-05-06 23:40" 
    for (i = 0; i < datapoints.length; i++) {
      datapoints[i].dataInicio = datapoints[i].dataInicio.replace(" ", "T");
      datapoints[i].dataFim    = datapoints[i].dataFim.replace(" ", "T");

      datapoints[i].dataInicio += "-03:00";
      datapoints[i].dataFim    += "-03:00";

    }

    // Sorts the data in cronological order
    datapoints.sort(function(x, y){
      return d3.descending(x.dataFim, y.dataFim);
    })

    // Nestes the data by government
    const nested = d3.nest()
      .key(function(d){
        return d.governo;
      })
      .entries(datapoints);

    /*
    Changes the h1 and the h5
    with the chart title and 
    party name details
    */

    if (scaleType === "todos") {
      d3.select(".viz-main-title")
        .html("Todos os partidos");

      d3.select(".viz-subtitle")
        .html("Agregado da Câmara");
    }
    else if (scaleType == "partidos") {

      var partyName = corresp["partidos"][entity]["name"];
      var partyDesc = corresp["partidos"][entity]["description"]

      d3.select(".viz-main-title")
        .html(entity);

      d3.select(".viz-subtitle")
        .html(partyDesc);

    }
    else if (scaleType === "deputados" ) {
        var depName  = corresp["deputados"][entity]["name"];
        var depParty = corresp["deputados"][entity]["party"];
        var depUF    = corresp["deputados"][entity]["uf"];
        d3.select(".viz-main-title")
          .html(`${depName}`);

        d3.select(".viz-subtitle")
          .html(`${depParty} - ${depUF}`)
    }


    // Creates a holder for the smaller charts
    const outerContainer = d3.select(targetDiv)
      .append("div")
      .attr("class", "outer-container")
      .attr("id", "outer-container");

    /*
    We have two sizes for the charts, one for mobile
    and one for desktop.
    */

    if (mobileScreen) {

      var margin = { top: 0, left: 0, right: 0, bottom: 20},
        height = 350 - margin.top - margin.bottom,
        width = 300 - margin.left - margin.right;

    }

    else {

      var margin = { top: 0, left: 0, right: 0, bottom: 20},
        height = 350 - margin.top - margin.bottom,
        width = 600 - margin.left - margin.right;

    }

    // Sets scales - notice that we are reading data from "escalas.json"

    // 2. xLeftwardScale / xRightwardScale
    if (scaleType == "todos")
      var xDomainMax = scales["todos"]

    else if (scaleType == "partidos")
      var xDomainMax = scales["partidos"]

    else if (scaleType == "deputados")
      var xDomainMax = scales["deputados"]

    const xLeftwardScale = d3.scaleLinear()
      .range( [ (width / 2) - 1, 0 ] )
      .domain([ 0,  xDomainMax ]);

    const xRightwardScale = d3.scaleLinear()
      .range([ (width / 2) + 1,  width ])
      .domain([ 0,  xDomainMax ]);

    const widthScale = d3.scaleLinear()
      .range( [0, width / 2])
      .domain([ 0, xDomainMax ] )

    /*
    Now the code gets a bit crazy. We discovered that d3.timeScale().ticks()
    will break Safari because it generates dates that are not ISO-formatted.
    This way, we used a scaleLinear to draw the bars using int epoch values.
    */


    if (isSafari) {

      /* 
      If the navigator is Safari, we can't use scaleTime because
      of a bug in yPositionScale.ticks() behavior.
      It would break the whole thing when requesting to draw custom axis annotations.
      */

      var yPositionScale = d3.scaleLinear()
        // domain will be set and updated when drawing each individual chart
        .range([height, 0]);

    }

    else {

      /*
      If we are not in Safari, it's safe to use scaleTime
      */

      var yPositionScale = d3.scaleTime()
        // domain will be set and updated when drawing each individual chart
        .range([height, 0]);

    }

    /* 
    The bar charts CAN'T have the same height
    since some of the data bins are smaller than others, time-wise.
    They can't be positioned evenly as well, for this same reason.
    That's why we will parse the dates when drawing the rects.
    */

    const heightScale = d3.scaleTime()
    // domain will be set and updated when drawing each individual chart
      .range([ 0, height ])

    // Creates a smaller chart for each government the entity was present
    const innerContainers = outerContainer.selectAll(".chart-container")
      .data(nested)
      .enter().append('div')
      .attr('class', 'chart-container');

    // Counts the votes in order to add informative labels
    var voteCounts = { }

    for (i = 0; i < nested.length; i++) {

      var votesToCount = nested[i].values;
      var supportCount = 0;
      var oppositionCount = 0;

      for (j = 0; j < votesToCount.length; j++) {
        supportCount    += +votesToCount[j].proGovCtg;
        oppositionCount += +votesToCount[j].antiGovCtg;
      }

      var totalVotes = supportCount + oppositionCount;
      var supportPercentage = Math.round(supportCount / totalVotes * 100)

      voteCounts[nested[i].key] = { 
        "supportCount"      : supportCount,  
        "oppositionCount"   : oppositionCount,
        "totalVotes"        : totalVotes,
        "supportPercentage" : supportPercentage
      }

    }

    // Appends the government count for the period
    innerContainers.append("div")
      .attr("class", "chart-support-count")
      .html(function(d){

        var value = voteCounts[d.key]["supportPercentage"];
        var htmlContent = `${value}% a favor do governo`
        return htmlContent;

      })

    // Appends a chart title
    innerContainers.append("div")
      .attr("class", "chart-title")
      .html(function(d){

        switch(d.key) {

          case "Lula 1":
            var html = '<span class=gov-name>Lula</span><span class="mandato">1º mandato</span>';
            break;
          case "Lula 2":
            var html = '<span class=gov-name>Lula</span><span class="mandato">2º mandato</span>';
            break;

          case "Dilma 1":
            var html = '<span class=gov-name>Dilma</span><span class="mandato">1º mandato</span>';
            break;

          case "Dilma 2":
            var html = '<span class=gov-name>Dilma</span><span class="mandato">2º mandato</span>';
            break;

          case "Temer 1":
            var html = '<span class=gov-name>Temer</span>';
            break;

          case "Bolsonaro 1":
            var html = '<span class=gov-name>Bolsonaro</span>';
            break;
        }

        return html;

      })

    // Adds a container for the labels
    const labelContainer = innerContainers
        .append("div")
        .attr("class", "label-container label-container-bar")

    labelContainer.append("span")
      .attr("class", "label-oposicao")
      .html("← Oposição")

    labelContainer.append("span")
      .attr("class", "label-aliado")
      .html("Aliado →")

    // Adds the svg – and the actual chart
    const barCharts = innerContainers.append("svg")
      .attr("class", "svg-chart")
      .attr("height", height + margin.bottom)
      .attr("width", width)
      .each(function(d){


        const element = d3.select(this);

        /*
        Each government will have its own yPositionScale domain
        */
        if (d.key === "Lula 1") {
          var startDate = new Date(2003, 0, 1);
          var endDate   = new Date(2006, 11, 31);
        }
        else if (d.key === "Lula 2") {
          var startDate = new Date(2007, 0, 1);
          var endDate   = new Date(2010, 11, 31);
        }
        else if (d.key === "Dilma 1") {
          var startDate = new Date(2011, 0, 1);
          var endDate   = new Date(2014, 11, 31);
        }
        else if (d.key === "Dilma 2") {
          var startDate = new Date(2015, 0, 1);
          var endDate   = new Date(2018, 11, 31);
        }
        else if (d.key === "Temer 1") {
          var startDate = new Date(2015, 0, 1);
          var endDate   = new Date(2018, 11, 31);
        }
        else if (d.key === "Bolsonaro 1") {
          var startDate = new Date(2019, 0, 1);
          var endDate   = new Date(2022, 11, 31);
        }

        yPositionScale.domain([ startDate, endDate ]);

        /*
         The height of each rect depends of the difference
         between the start date and end date of each bin/datapoint.
         Since we are using date objects, we can simply subtract them
         and use the resulting integers to calculate
         a maximum possible range
        */

        heightScale.domain([0, (endDate - startDate)]);

        // Adds bars

        // Opposition bars
        element.selectAll(".bar-leftward")
          .data(d.values)
          .enter().append("rect")
          .attr("class", "bar-leftward")
          .attr("x", function(d){
            return xLeftwardScale(0) - widthScale( +d.antiGovCtg );
          })
          .attr("width", function(d){
            return widthScale(+d.antiGovCtg);
          })
          .attr("y", function(d){
            return yPositionScale( new Date(d.dataFim) );
          })
          .attr("height", function(d) {
            return heightScale( new Date(d.dataFim) - new Date(d.dataInicio) );
          })
          .attr("fill", "#c441c4")
          .attr("opacity", .7)
          .style("shape-rendering", "crispEdges")
          .attr("data-tippy-content", function(d){

            var monthYear = new Date(d.dataInicio)
              .toLocaleDateString("pt-BR", {month : "long", year: "numeric"})
              .capitalize();

            if (scaleType == "todos") { 
              var name = "Todos os partidos";
              var info = "";
            }
            else if (scaleType == "deputados") {
              var name = `${d.parlamentar}`;
              var info = `${d.partido} | ${d.uf}`;
            }
            else if (scaleType == "partidos") {
              var name = `${d.partido}`
              var info = "";
            }

            var htmlContent = `
            <span class="tooltip-name">${monthYear}</span></br>
            <span class="tooltip-long-desc">${d.antiGovCtg} votos <strong class="against">contra</strong> o governo</br>
            <strong>${Math.round(d.antiGovPct * 100)}%</strong> de oposição no período</br>
            `
            return htmlContent;
          })
          .on("mouseover", function(d){

            // Highlights the current selection by lowering the opacity of all others
            d3.select(this)
              .attr("opacity", 1);

          })
          .on("mouseout", function(d){

            // Un-highlights the current selection
            d3.select(this)
              .attr("opacity", .7)

          });

        // Adds situation bars
        element.selectAll(".bar-rightward")
          .data(d.values)
          .enter().append("rect")
          .attr("class", "bar-rightward")
          .attr("x", function(d){
            return xRightwardScale(0);
          })
          .attr("width", function(d) {
            return widthScale( +d.proGovCtg );
          })
          .attr("y", function(d){
            return yPositionScale( new Date(d.dataFim) );
          })
          .attr("height", function(d) {
            return heightScale( new Date(d.dataFim) - new Date(d.dataInicio) );
          })
          .attr("fill", "#00a79d")
          .attr("opacity", .6)
          .style("shape-rendering", "crispEdges")
          .attr("data-tippy-content", function(d){

            var monthYear = new Date(d.dataInicio)
              .toLocaleDateString("pt-BR", {month : "long", year: "numeric"})
              .capitalize();

            if (scaleType == "todos") { 
              var name = "Todos os partidos";
              var info = "";
            }
            else if (scaleType == "deputados") {
              var name = `${d.parlamentar}`;
              var info = `${d.partido} | ${d.uf}`;
            }
            else if (scaleType == "partidos") {
              var name = `${d.partido}`
              var info = "";
            }

            var htmlContent = `
            <span class="tooltip-name">${monthYear}</span></br>
            <span class="tooltip-long-desc">${d.proGovCtg} votos <strong class="pro">a favor</strong> do governo</br>
            <strong>${Math.round(d.proGovPct * 100)}%</strong> de governismo no período</br>
            `
            return htmlContent;

          })
          .on("mouseover", function(d){

            // Highlights the current selection by lowering the opacity of all others
            d3.select(this)
              .attr("opacity", 1);

          })
          .on("mouseout", function(d){

            // Un-highlights the current selection
            d3.select(this)
              .attr("opacity", .6)

          });

        // Adds a line that goes from top to bottom in the charts
        element.append("line")
          .attr("class", ".chart-spine")
          .attr("x1", width / 2)
          .attr("x2", width / 2)
          .attr("y1", 0 + 2)
          .attr("y2", height - 2)
          .attr("stroke", "rgb(188, 199, 207)")
          .attr("stroke-width", 2)


        // Defining the custom axis

        /*
        We need to select only the ticks which point to January, that
        is, to the beggining of a year.
        Will do that by populating an array with the values we want
        and filtering out all others.
        */

        const yAxisTicks = [ ];
        if (!isSafari) {
          // If not in Safari, we can deal with the time ticks
          for (i = 0; i <  yPositionScale.ticks().length; i++) {
            var date = yPositionScale.ticks()[i];
            if ( date.getMonth() == 0) {
              yAxisTicks.push(date);
            }
          }

        }

        if (isSafari) {
          // If we are in Safari, we need to do some more stuff
          // because of the d3.scaleTime().ticks() behavior I mentioned earlier

          var years = [ ];

          for (i = 0; i <  yPositionScale.ticks().length; i++) {

            // Gets the date out of the tick
            var date = new Date(yPositionScale.ticks()[i]);

            // Builds a new date for the first of January of that year
            var year = ''
            if ( !years.includes( date.getFullYear() ) )  {
              
              year = date.getFullYear();

              date = new Date(year, 0, 1);

              years.push(year);

              yAxisTicks.push(date);

            }

          }

        }

        // Adds the yAxis
        const yAxis = d3.axisLeft(yPositionScale)
          .tickValues(yAxisTicks)
          .tickFormat( d3.timeFormat("%Y") )
          .tickSize(-width);
        element.append("g")
          .attr("class", "axis y-axis")
          .call(yAxis);

        var yAxisLabels = d3.selectAll(".y-axis")
          .selectAll("text")
          .attr("class", "axis-label y-axis-label")
          .attr("fill",  "rgb(188, 199, 207)")
          .attr("dy", -36)
          .attr("dx", 35);


        /*
        For the xAxis, we need to define which values to show as well.
        They are relative to which scaleType we are using, so we will round the
        xDomainMax to the nearest hundred/thousand. Then, we will position
        the text at the borders of the cart, so we can style it more freely –
        even though we lose a bit of precision by doing so.
        */

        if (scaleType == "deputados") {
          var scaleTypeTick = Math.round(xDomainMax / 10) * 10;
        }
        else {
          var scaleTypeTick = Math.round(xDomainMax / 1000) * 1000;
        }

        var xAxis = element.append("g")
          .attr("class", "x-axis")

        xAxis.append("text")
          .text("0")
          .attr("class", "axis-label x-axis-label")
          .attr("text-anchor", "middle")
          .attr("x", width / 2)
          .attr("y", height)
          .attr("dy", 20);

        xAxis.append("text")
          .text(scaleTypeTick)
          .attr("class", "axis-label x-axis-label")
          .attr("text-anchor", "middle")
          .attr("x", width)
          .attr("y", height)
          .attr("dy", 20)
          .attr("dx", -18);

        xAxis.append("text")
          .text(scaleTypeTick)
          .attr("class", "axis-label x-axis-label")
          .attr("text-anchor", "middle")
          .attr("x", 0)
          .attr("y", height)
          .attr("dy", 20)
          .attr("dx", 15);

        // Adds baselines
        element.append("line")
          .attr("class", "chart-baseline")
          .attr("x1", 0)
          .attr("x2", width)
          .attr("y1", 0)
          .attr("y2", 0)
          .attr("stroke", "rgb(188, 199, 207)")
          .attr("stroke-dasharray", "1,2");

        element.append("line")
          .attr("class", "chart-baseline")
          .attr("x1", 0)
          .attr("x2", width)
          .attr("y1", height)
          .attr("y2", height)
          .attr("stroke", "rgb(188, 199, 207)")
          .attr("stroke-dasharray", "1,2");

      })

    // For each bar chart, adds a bottom div with the support and opposition count
    var countContainers = innerContainers.append("div")
      .attr("class", "label-container label-container-bottom")

    countContainers.append("span")
      .attr("class", "label-oposicao")
      .html(function(d){

        var value = voteCounts[d.key]["oppositionCount"];
        var htmlContent = `${value} votos`
        return htmlContent;

      })

    countContainers.append("span")
      .attr("class", "label-aliado")
      .html(function(d){

        var value = voteCounts[d.key]["supportCount"];
        var htmlContent = `${value} votos`
        return htmlContent;

      })

  // Initiates the tooltip object
  // See https://atomiks.github.io/tippyjs/
  tippy("[data-tippy-content]", {
    arrow: true,
    theme: 'basometro',
    maxWidth: '250px',
  });

  // Displays everything again
  d3.select(".bar-container").style("opacity", 1);
  d3.select('.viz-titles').style("opacity", 1);

  // Hides the loading button
  d3.select(".lds-dual-ring").classed("loading", false);

  }

}
