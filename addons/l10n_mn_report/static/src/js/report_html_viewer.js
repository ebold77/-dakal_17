odoo.define('l10n_mn_report.oderp_report_excel_output', function (require) {
    "use strict";
    var core = require('web.core');
    var form_widget = require('web.form_widgets');
    var form_common = require('web.form_common');
    var formats = require('web.formats');
    var Model = require('web.Model');
    var QWeb = core.qweb;
    var _t = core._t;
    var this_ = this;
// xls тайланг дэлгэцээр харах функц
    function html_report(){
        if(this_.field_manager.datarecord.id){
            var model = new Model(this_.field_manager.model);
            var model_id = this_.field_manager.datarecord.id
            model.call("set_report_id",[model_id]).then(function(){
                model.call("get_report_data",[model_id]).then(function(data){
                    model.call("get_report_merge",[model_id]).then(function(merged_cells){
                        data = JSON.parse(data);
                        merged_cells = JSON.parse(merged_cells);
                        document.getElementsByClassName("modal-dialog modal-lg")[0].style.width = "100%";
                        data.unshift(['']);
                        for(var i in data[1]){
                            data[0].unshift("");
                        }
                        for (var i in data){
                            data[i].unshift('');
                        }

                        var mergedCells = [{}];
                        var colWidths = [];
                        for (var i in merged_cells){
                            colWidths.push(100);
                            mergedCells.push({row : merged_cells[i][0], col:merged_cells[i][1],rowspan:merged_cells[i][2], colspan:merged_cells[i][3]});
                        }
                        mergedCells.shift();
                        var container = document.getElementById('report_output_see');
                        container.innerHTML = "";
                        var hot = new Handsontable(container, {
                          data: data,
                          rowHeaders: true,
                          colHeaders: true,
                          manualColumnResize: colWidths,
                          readOnly:true,
                          filters: true,
                          className: "htLeft",
                          dropdownMenu: true,
                          mergeCells:mergedCells
                        });
                    });
                });
            });
        }
        else{
            setTimeout(html_report, 500); // check again in a second
        }
    };
    form_widget.WidgetButton.include({
        on_click:function(node) {
            if(this.node.attrs.class === "btn-primary see_report"){
                this._super();
                this_ = this;
                html_report();
            }
            else{
                this._super();
            }
        },
    });
});