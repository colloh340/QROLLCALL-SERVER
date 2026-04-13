
  
function createLineChart(element, values){
 // Line Chart
 var lineOptions = {
    chart: {
        type: 'line',
        height: 350,
        width: '100%',
        responsive: true,
    },
    series: [{
        name: values["name"],
        data: values["data"] // Dummy data for past 7 weeks
        }],
        xaxis: {
        categories: values["categories"],
        },
        // title: {
        //     text: 'Trends',
        //     align: 'start',
        //     style: {
        //         fontSize: '18px',
        //     },
        // },
        colors: ['#007BFF'], // Blue color for the line
        markers: {
            size: 4,
            colors: ['#007BFF'],
            strokeColors: '#fff',
            strokeWidth: 2,
        },
        responsive: [{
        breakpoint: 756, // Adjust settings for smaller screens
        options: {
            chart: {
            height: 300,
            },
            markers: {
            size: 3,
            },
        },
        }],
    };

    var lineChart = new ApexCharts(document.querySelector(`#${element}`), lineOptions);
    lineChart.render();
}
function createDonutChart(element, labels, value){
    const ctx = document.getElementById(element).getContext('2d');
    const data = {
        labels: labels,
        datasets: [{
            label: 'Attendance Distribution',
            data: value, // Dummy data
            backgroundColor: ['#4CAF50', '#F44336'],
        }]
    };

    const config = {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
        }
    };

    // Create the chart
    const chart = new Chart(ctx, config);

    // Ensure chart resizes properly on window resize
    window.addEventListener('resize', function() {
        chart.resize();
    });
}
function createGuageChart(element, value, label){
    var options = {
        chart: {
          type: 'radialBar',
          height: 350,
        },
        series: [value], // Dummy data: 75% compliance
        labels: [label],
        plotOptions: {
          radialBar: {
            startAngle: -90,
            endAngle: 90,
            hollow: {
              margin: 15,
              size: '70%',
            },
            dataLabels: {
              name: {
                fontSize: '18px',
                color: '#000',
                offsetY: -10,
              },
              value: {
                fontSize: '22px',
                color: '#000',
                offsetY: 10,
                formatter: function (val) {
                  return `${val}%`;
                },
              },
            },
          },
        },
        colors: ['#4CAF50'], // Green color for the gauge
      };
    
      var gauge_chart = new ApexCharts(document.querySelector(`#${element}`), options);
      gauge_chart.render();
}

function delayedRedirect(url) {
  //$('#modal-loading').modal('show');

  // Store flag in sessionStorage to remember the modal should be closed
  //sessionStorage.setItem('modalClosed', 'true');

  window.location.href = url;
}

// Ensure modal stays closed when user navigates back
window.onload = function () {
  if (sessionStorage.getItem('modalClosed') === 'true') {
      $('#modal-loading').modal('hide');
      sessionStorage.removeItem('modalClosed'); // Reset flag
  }
};

function createToast(message, status){
  var toast = document.createElement('div');
  toast.classList.add('position-fixed');
  //toast.classList.add('top-0');
  toast.style.top = "56px"
  toast.classList.add('end-0','p-3')
  toast.style.zIndex = "10000";
  toast.style.maxWidth = "100vw"
  var bg_color = "bg-danger"
  if (status == 300){
      bg_color = "bg-info"
  }else if(status == 200 || status == 201){
      bg_color = "bg-success"
  }
  var toast_html = `
  <div id="liveToast" class="toast hide ${bg_color}" role="alert" aria-live="assertive" aria-atomic="true">
  <div class="toast-header">
      <strong class="me-auto">QrollCall</strong>
      <small>Now</small>
      <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
  </div>
  <div class="toast-body text-light">
      ${message}
  </div>
  </div>
  `
  toast.innerHTML = toast_html
  document.getElementById("body").appendChild(toast)
  $("#liveToast").show()
  setTimeout(function(){
      toast.remove()
  },5500)

}

function isStrongPassword(password) {
  const minLength = 6;
  const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{6,}$/;

  return password.length >= minLength && regex.test(password);
}