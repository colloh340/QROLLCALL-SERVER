$(document).ready(async function(){
    

    const lineChart = document.getElementById("lineChart");
    if(lineChart){
        lineChart.innerHTML = '<i class="fa-solid fs-5 fa-spinner fa-spin-pulse text-center"></i>';
    }
    // load today classes
    try{
        const response = await fetch('/dashboard?get=data',{
                method: "GET"
        });
        const data = await response.json();
        const status = data.status;
        
        lineChart.innerHTML = '';

        if(status === 200 || status === 201){
            const report = data.report;
            var graph_y = [];
            var graph_x = [];
            const name = "Attendance";

            console.log("Report: "+report);

            if(report.units != null){
                 report.units.forEach(unit => {
                    graph_y.push(unit.total_compliance_percentage);
                    graph_x.push(unit.unit_code);
                });
                createLineChart("lineChart",{
                    "name":name,
                    "data":graph_y,
                    "categories":graph_x
                });
            }else{
                lineChart.innerHTML = 'No attendance summary.';
            }
           
        }else{
            const message = data.message;
            createToast(message, status);
        }
    }catch(error){
        lineChart.innerHTML = 'Failed to fetch data.';
        console.log("Dashboard Error: "+error)
    }
    

})