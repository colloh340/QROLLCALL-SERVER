$(document).ready(function(){
    
    createGuageChart("gaugeChart", 75, "Compliance");
    createDonutChart("attendance-distribution", ['Present', 'Absent'], [75, 25]);
    createLineChart("lineChart",{
        "name":"Attendance",
        "data":[45, 52, 38, 45, 19, 23, 2],
        "categories":['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7']
    })     
});